"""CLI wrapper for OpenFraud forensic analysis."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from openfraud.core.forensics import (
    calculate_benford_ssd,
    calculate_z_score,
    calculate_velocity_score,
    detect_frozen_ledger,
)


def main():
    parser = argparse.ArgumentParser(description="OpenFraud Forensics CLI")
    parser.add_argument("--data-path", required=True)
    parser.add_argument("--amount-column", required=True)
    parser.add_argument(
        "--analysis-type",
        required=True,
        choices=["benford", "zscore", "velocity", "frozen_ledger", "all"],
    )
    parser.add_argument("--entity-column")
    parser.add_argument("--date-column")
    parser.add_argument("--expected-max", type=float, default=100.0)
    parser.add_argument("--min-consecutive", type=int, default=3)
    args = parser.parse_args()

    path = Path(args.data_path)
    if args.data_path.endswith(".csv"):
        df = pd.read_csv(args.data_path)
    else:
        df = pd.read_parquet(args.data_path)

    amounts = df[args.amount_column].dropna().to_numpy()
    result = {}

    if args.analysis_type in ("benford", "all"):
        result["benford_ssd"] = calculate_benford_ssd(amounts)
        result["benford_flag"] = result["benford_ssd"] > 0.1

    if args.analysis_type in ("zscore", "all"):
        mean = float(np.mean(amounts))
        std = float(np.std(amounts))
        z_scores = {
            str(i): float(calculate_z_score(v, mean, std)) for i, v in enumerate(amounts[:50])
        }
        outliers = [float(v) for v in amounts[:50] if abs(calculate_z_score(v, mean, std)) > 3]
        result["zscore_mean"] = mean
        result["zscore_std"] = std
        result["zscore_sample"] = z_scores
        result["zscore_outliers"] = outliers

    if args.analysis_type in ("velocity", "all"):
        if args.entity_column and args.date_column:
            df[args.date_column] = pd.to_datetime(df[args.date_column])
            df["period"] = df[args.date_column].dt.to_period("D")
            velocity = df.groupby([args.entity_column, "period"]).size().reset_index(name="count")
            events = velocity["count"].to_numpy()
            result["velocity_score"] = calculate_velocity_score(events, args.expected_max)
            result["velocity_max"] = int(np.max(events))
        else:
            result["velocity_error"] = (
                "entity-column and date-column required for velocity analysis"
            )

    if args.analysis_type in ("frozen_ledger", "all"):
        if args.entity_column and args.date_column:
            df_sorted = df.sort_values(by=args.date_column)
            frozen = []
            for entity, group in df_sorted.groupby(args.entity_column):
                ledger = group[args.amount_column].to_numpy()
                if detect_frozen_ledger(ledger, args.min_consecutive):
                    frozen.append(str(entity))
            result["frozen_ledger_entities"] = frozen
            result["frozen_ledger_count"] = len(frozen)
        else:
            result["frozen_ledger"] = detect_frozen_ledger(amounts, args.min_consecutive)

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
