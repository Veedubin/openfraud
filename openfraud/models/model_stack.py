"""
openfraud/models/model_stack.py
Machine Learning Pipeline for Fraud Detection
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import json

from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    average_precision_score,
    precision_recall_curve,
    classification_report,
    roc_auc_score,
)

import lightgbm as lgb


def train_fraud_model(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str,
    entity_id_col: str,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[lgb.LGBMClassifier, Dict]:
    """
    Train a LightGBM fraud detection model.

    Args:
        df: Input dataframe with features and target
        feature_cols: List of feature column names
        target_col: Name of target column (binary fraud indicator)
        entity_id_col: Column name for entity identifiers
        test_size: Fraction of data for testing
        random_state: Random seed

    Returns:
        Tuple of (trained_model, metrics_dict)
    """
    # Prepare data
    X = df[feature_cols].copy()
    y = df[target_col].copy()

    # Handle missing values
    X = X.fillna(X.median())

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # Calculate scale_pos_weight for imbalanced data
    fraud_rate = y_train.mean()
    scale_pos_weight = (1 - fraud_rate) / fraud_rate if fraud_rate > 0 else 1.0

    print(f"Training set fraud rate: {fraud_rate:.4f}")
    print(f"Scale pos weight: {scale_pos_weight:.2f}")

    # Train model
    model = lgb.LGBMClassifier(
        objective="binary",
        boosting_type="gbdt",
        num_leaves=31,
        max_depth=-1,
        learning_rate=0.05,
        n_estimators=200,
        class_weight="balanced",
        scale_pos_weight=scale_pos_weight,
        random_state=random_state,
        n_jobs=-1,
        verbose=-1,
    )

    model.fit(X_train, y_train)

    # Predictions
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)

    # Metrics
    auprc = average_precision_score(y_test, y_pred_proba)
    auroc = roc_auc_score(y_test, y_pred_proba)

    metrics = {
        "auprc": float(auprc),
        "auroc": float(auroc),
        "fraud_rate": float(fraud_rate),
        "n_train": len(X_train),
        "n_test": len(X_test),
    }

    print(f"\nModel Performance:")
    print(f"  AUPRC: {auprc:.4f}")
    print(f"  AUROC: {auroc:.4f}")

    # Feature importance
    importance = pd.DataFrame(
        {
            "feature": feature_cols,
            "importance": model.feature_importances_,
        }
    ).sort_values("importance", ascending=False)

    print(f"\nTop 10 Important Features:")
    print(importance.head(10).to_string(index=False))

    return model, metrics


def calibrate_model(
    model: lgb.LGBMClassifier,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    method: str = "isotonic",
) -> CalibratedClassifierCV:
    """
    Calibrate model probabilities for reliable risk scores.

    Args:
        model: Trained model
        X_val: Validation features
        y_val: Validation targets
        method: 'isotonic' or 'sigmoid'

    Returns:
        Calibrated classifier
    """
    calibrated = CalibratedClassifierCV(model, method=method, cv="prefit")
    calibrated.fit(X_val, y_val)
    return calibrated


def get_risk_tiers(
    probabilities: np.ndarray,
    high_threshold: float = 0.7,
    medium_threshold: float = 0.3,
) -> np.ndarray:
    """
    Assign risk tiers based on predicted probabilities.

    Args:
        probabilities: Fraud probabilities (0-1)
        high_threshold: Threshold for HIGH risk tier
        medium_threshold: Threshold for MEDIUM risk tier

    Returns:
        Array of risk tier labels
    """
    tiers = np.where(
        probabilities >= high_threshold,
        "HIGH",
        np.where(probabilities >= medium_threshold, "MEDIUM", "LOW"),
    )
    return tiers


def cross_validate_model(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str,
    n_splits: int = 5,
    random_state: int = 42,
) -> Dict:
    """
    Perform stratified cross-validation for robust evaluation.

    Args:
        df: Input dataframe
        feature_cols: Feature column names
        target_col: Target column name
        n_splits: Number of CV folds
        random_state: Random seed

    Returns:
        Dictionary with CV metrics
    """
    X = df[feature_cols].fillna(df[feature_cols].median())
    y = df[target_col]

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    scores = {"auprc": [], "auroc": []}

    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

        model = lgb.LGBMClassifier(
            objective="binary",
            class_weight="balanced",
            random_state=random_state,
            verbose=-1,
        )
        model.fit(X_train, y_train)

        y_proba = model.predict_proba(X_val)[:, 1]
        scores["auprc"].append(average_precision_score(y_val, y_proba))
        scores["auroc"].append(roc_auc_score(y_val, y_proba))

        print(
            f"Fold {fold + 1}: AUPRC={scores['auprc'][-1]:.4f}, AUROC={scores['auroc'][-1]:.4f}"
        )

    print(
        f"\nCV Mean: AUPRC={np.mean(scores['auprc']):.4f}, AUROC={np.mean(scores['auroc']):.4f}"
    )

    return {
        "auprc_mean": float(np.mean(scores["auprc"])),
        "auprc_std": float(np.std(scores["auprc"])),
        "auroc_mean": float(np.mean(scores["auroc"])),
        "auroc_std": float(np.std(scores["auroc"])),
    }


def save_model(
    model: lgb.LGBMClassifier, filepath: Path, metrics: Optional[Dict] = None
):
    """
    Save trained model to disk.

    Args:
        model: Trained LightGBM model
        filepath: Path to save model
        metrics: Optional metrics dictionary to save alongside
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    model.booster_.save_model(str(filepath))

    if metrics:
        metrics_path = filepath.with_suffix(".metrics.json")
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)

    print(f"Model saved to {filepath}")


def load_model(filepath: Path) -> lgb.LGBMClassifier:
    """
    Load trained model from disk.

    Args:
        filepath: Path to saved model

    Returns:
        Loaded LightGBM model
    """
    model = lgb.LGBMClassifier()
    model.booster_ = lgb.Booster(model_file=str(filepath))
    return model
