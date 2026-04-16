"""
openfraud/utils/data_utils.py
Data loading and preprocessing utilities.
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict
from pathlib import Path


def load_parquet_chunks(
    filepath: Path, chunk_size: int = 100000, columns: Optional[List[str]] = None
):
    """
    Load a Parquet file in chunks for memory efficiency.

    Args:
        filepath: Path to Parquet file
        chunk_size: Number of rows per chunk
        columns: Optional column subset to load

    Yields:
        DataFrame chunks
    """
    import pyarrow.parquet as pq

    parquet_file = pq.ParquetFile(filepath)

    for batch in parquet_file.iter_batches(batch_size=chunk_size, columns=columns):
        yield batch.to_pandas()


def calculate_derived_features(
    df: pd.DataFrame,
    numerator: str,
    denominator: str,
    output_name: str,
    handle_zero: str = "fill_zero",
) -> pd.DataFrame:
    """
    Calculate ratio features with proper zero handling.

    Args:
        df: Input DataFrame
        numerator: Numerator column name
        denominator: Denominator column name
        output_name: Name for new ratio column
        handle_zero: How to handle zero denominator ('fill_zero', 'fill_nan', 'skip')

    Returns:
        DataFrame with new ratio column
    """
    df = df.copy()

    if handle_zero == "fill_zero":
        df[output_name] = np.where(
            df[denominator] > 0, df[numerator] / df[denominator], 0.0
        )
    elif handle_zero == "fill_nan":
        df[output_name] = df[numerator] / df[denominator].replace(0, np.nan)
    elif handle_zero == "skip":
        df[output_name] = df[numerator] / df[denominator]
        df.loc[df[denominator] == 0, output_name] = np.nan

    return df


def aggregate_by_entity(
    df: pd.DataFrame, entity_col: str, agg_dict: Dict[str, str]
) -> pd.DataFrame:
    """
    Aggregate transaction data to entity level.

    Args:
        df: Transaction-level DataFrame
        entity_col: Column to group by (e.g., 'account_id')
        agg_dict: Dictionary of {column: aggregation_function}

    Returns:
        Entity-level aggregated DataFrame
    """
    return df.groupby(entity_col, as_index=False).agg(agg_dict)


def add_peer_group_stats(
    df: pd.DataFrame, group_col: str, value_col: str, prefix: str = "peer"
) -> pd.DataFrame:
    """
    Add peer group statistics (mean, median, std) to DataFrame.

    Args:
        df: Input DataFrame
        group_col: Column defining peer groups
        value_col: Column to calculate statistics on
        prefix: Prefix for new columns

    Returns:
        DataFrame with peer statistics columns
    """
    df = df.copy()

    stats = (
        df.groupby(group_col)[value_col].agg(["mean", "median", "std"]).reset_index()
    )
    stats.columns = [group_col, f"{prefix}_mean", f"{prefix}_median", f"{prefix}_std"]

    df = df.merge(stats, on=group_col, how="left")

    # Calculate z-score
    df[f"{prefix}_z_score"] = (df[value_col] - df[f"{prefix}_mean"]) / df[
        f"{prefix}_std"
    ]
    df[f"{prefix}_z_score"] = df[f"{prefix}_z_score"].fillna(0)

    # Calculate relative ratio
    df[f"{prefix}_relative_ratio"] = df[value_col] / df[f"{prefix}_median"]
    df[f"{prefix}_relative_ratio"] = df[f"{prefix}_relative_ratio"].fillna(1.0)

    return df


def split_temporal(
    df: pd.DataFrame, date_col: str, train_frac: float = 0.7, val_frac: float = 0.15
) -> tuple:
    """
    Split data temporally for time-series aware train/val/test.

    Args:
        df: DataFrame with date column
        date_col: Name of date column
        train_frac: Fraction for training
        val_frac: Fraction for validation (remainder goes to test)

    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    df = df.sort_values(date_col)

    n = len(df)
    train_end = int(n * train_frac)
    val_end = int(n * (train_frac + val_frac))

    train_df = df.iloc[:train_end]
    val_df = df.iloc[train_end:val_end]
    test_df = df.iloc[val_end:]

    return train_df, val_df, test_df


def save_results(df: pd.DataFrame, filepath: Path, format: str = "parquet"):
    """
    Save results to file.

    Args:
        df: DataFrame to save
        filepath: Output path
        format: 'parquet' or 'csv'
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if format == "parquet":
        df.to_parquet(filepath, index=False)
    elif format == "csv":
        df.to_csv(filepath, index=False)
    else:
        raise ValueError(f"Unknown format: {format}")

    print(f"Saved {len(df)} rows to {filepath}")
