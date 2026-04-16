"""
Generate sample data for testing OpenFraud.
Creates synthetic transaction data with known fraud patterns.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import argparse


def generate_normal_transactions(
    n_entities: int = 1000,
    n_transactions: int = 50000,
    start_date: datetime = None,
    fraud_rate: float = 0.02,
) -> pd.DataFrame:
    """
    Generate synthetic transaction data with embedded fraud patterns.

    Args:
        n_entities: Number of unique entities (users/accounts)
        n_transactions: Total number of transactions
        start_date: Start date for transactions
        fraud_rate: Percentage of fraudulent entities

    Returns:
        DataFrame with transactions
    """
    if start_date is None:
        start_date = datetime.now() - timedelta(days=365)

    np.random.seed(42)

    # Create entity profiles
    n_fraud_entities = int(n_entities * fraud_rate)
    n_normal_entities = n_entities - n_fraud_entities

    normal_entities = [f"ENT_{i:05d}" for i in range(n_normal_entities)]
    fraud_entities = [f"ENT_{i + n_normal_entities:05d}" for i in range(n_fraud_entities)]

    all_entities = normal_entities + fraud_entities
    entity_types = np.random.choice(["individual", "business"], size=n_entities)

    # Generate transactions
    transactions = []

    for _ in range(n_transactions):
        # Pick entity (fraud entities slightly more active)
        if np.random.random() < 0.3 and fraud_entities:
            entity = np.random.choice(fraud_entities)
        else:
            entity = np.random.choice(all_entities)

        is_fraud = entity in fraud_entities
        entity_idx = all_entities.index(entity)
        entity_type = entity_types[entity_idx]

        # Generate timestamp
        days_offset = np.random.randint(0, 365)
        hour = np.random.randint(0, 24)
        timestamp = start_date + timedelta(days=int(days_offset), hours=int(hour))

        # Generate amount (fraud = higher amounts or round numbers)
        if is_fraud and np.random.random() < 0.5:
            # Round number fraud
            amount = np.random.choice([100, 500, 1000, 5000, 10000])
        else:
            # Normal log-normal distribution
            amount = np.random.lognormal(4, 1.5)  # ~$50 median

        # Generate other fields
        status = np.random.choice(
            ["completed", "completed", "completed", "failed"], p=[0.7, 0.2, 0.05, 0.05]
        )

        # Velocity pattern for fraud
        if is_fraud:
            velocity = np.random.poisson(20)  # High velocity
        else:
            velocity = np.random.poisson(3)  # Normal velocity

        transaction = {
            "transaction_id": f"TXN_{len(transactions):08d}",
            "entity_id": entity,
            "entity_type": entity_type,
            "timestamp": timestamp,
            "amount": round(amount, 2),
            "status": status,
            "velocity_24h": velocity,
            "is_fraud": is_fraud,
        }

        transactions.append(transaction)

    df = pd.DataFrame(transactions)
    df = df.sort_values("timestamp").reset_index(drop=True)

    return df


def generate_frozen_ledger_pattern(base_df: pd.DataFrame, n_entities: int = 10) -> pd.DataFrame:
    """
    Add frozen ledger pattern to some entities.

    Args:
        base_df: Base transaction DataFrame
        n_entities: Number of entities to add pattern to

    Returns:
        Modified DataFrame
    """
    df = base_df.copy()

    # Select random entities
    frozen_entities = np.random.choice(df["entity_id"].unique(), size=n_entities, replace=False)

    for entity in frozen_entities:
        entity_mask = df["entity_id"] == entity
        entity_df = df[entity_mask]

        if len(entity_df) >= 3:
            # Pick an amount and repeat it
            frozen_amount = entity_df["amount"].iloc[0]

            # Set last 3+ transactions to same amount
            idx_to_modify = entity_df.index[-3:]
            df.loc[idx_to_modify, "amount"] = frozen_amount

    return df


def generate_network_relationships(
    n_nodes: int = 500,
    n_edges: int = 2000,
) -> pd.DataFrame:
    """
    Generate synthetic network relationships.

    Args:
        n_nodes: Number of nodes
        n_edges: Number of edges

    Returns:
        DataFrame with edges
    """
    np.random.seed(42)

    edges = []

    for _ in range(n_edges):
        source = f"NODE_{np.random.randint(0, n_nodes)}"
        target = f"NODE_{np.random.randint(0, n_nodes)}"

        # Avoid self-loops for most, add some intentionally
        if source == target and np.random.random() > 0.1:
            continue

        edge = {
            "source": source,
            "target": target,
            "relationship_type": np.random.choice(["transacted", "shared_device", "referred"]),
            "weight": np.random.random(),
        }

        edges.append(edge)

    return pd.DataFrame(edges)


def main():
    parser = argparse.ArgumentParser(description="Generate sample fraud data")
    parser.add_argument("--output-dir", type=str, default="./sample_data", help="Output directory")
    parser.add_argument("--n-entities", type=int, default=1000, help="Number of entities")
    parser.add_argument("--n-transactions", type=int, default=50000, help="Number of transactions")
    parser.add_argument("--fraud-rate", type=float, default=0.02, help="Fraud rate (0-1)")

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating sample data...")
    print(f"  Entities: {args.n_entities}")
    print(f"  Transactions: {args.n_transactions}")
    print(f"  Fraud rate: {args.fraud_rate}")

    # Generate transactions
    df = generate_normal_transactions(
        n_entities=args.n_entities,
        n_transactions=args.n_transactions,
        fraud_rate=args.fraud_rate,
    )

    # Add frozen ledger patterns
    df = generate_frozen_ledger_pattern(df, n_entities=10)

    # Save transactions
    transactions_path = output_dir / "transactions.parquet"
    df.to_parquet(transactions_path, index=False)
    print(f"\nSaved transactions to {transactions_path}")

    # Generate network data
    network_df = generate_network_relationships()
    network_path = output_dir / "network_edges.parquet"
    network_df.to_parquet(network_path, index=False)
    print(f"Saved network edges to {network_path}")

    # Print summary
    print(f"\nData Summary:")
    print(f"  Total transactions: {len(df)}")
    print(f"  Fraudulent transactions: {df['is_fraud'].sum()} ({df['is_fraud'].mean() * 100:.2f}%)")
    print(f"  Unique entities: {df['entity_id'].nunique()}")
    print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"  Total amount: ${df['amount'].sum():,.2f}")

    # Entity-level aggregation
    entity_df = (
        df.groupby("entity_id")
        .agg(
            {
                "amount": ["sum", "count", "mean"],
                "is_fraud": "first",
            }
        )
        .reset_index()
    )
    entity_df.columns = ["entity_id", "total_amount", "transaction_count", "avg_amount", "is_fraud"]

    entity_path = output_dir / "entities.parquet"
    entity_df.to_parquet(entity_path, index=False)
    print(f"\nSaved entity aggregation to {entity_path}")


if __name__ == "__main__":
    main()
