"""CLI wrapper for OpenFraud ML training."""

import argparse
import json
from pathlib import Path

import pandas as pd

from openfraud.models.model_stack import (
    train_fraud_model,
    cross_validate_model,
    save_model,
)


def main():
    parser = argparse.ArgumentParser(description="OpenFraud ML CLI")
    parser.add_argument("--data-path", required=True)
    parser.add_argument("--feature-cols", required=True)
    parser.add_argument("--target-col", required=True)
    parser.add_argument("--entity-id-col", required=True)
    parser.add_argument("--output-path")
    parser.add_argument("--cross-validate", action="store_true")
    args = parser.parse_args()

    df = (
        pd.read_csv(args.data_path)
        if args.data_path.endswith(".csv")
        else pd.read_parquet(args.data_path)
    )
    feature_cols = [c.strip() for c in args.feature_cols.split(",")]

    if args.cross_validate:
        metrics = cross_validate_model(df, feature_cols, args.target_col)
    else:
        model, metrics = train_fraud_model(df, feature_cols, args.target_col, args.entity_id_col)
        if args.output_path:
            save_model(model, Path(args.output_path), metrics)

    print(json.dumps(metrics, indent=2, default=str))


if __name__ == "__main__":
    main()
