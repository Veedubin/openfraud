"""
openfraud/graph/ingest.py
Graph database ingestion utilities for Memgraph.
"""

import pandas as pd
from typing import Dict, List, Optional
from memgraph_toolbox.api.memgraph import Memgraph


def ingest_nodes(
    db: Memgraph,
    df: pd.DataFrame,
    label: str,
    id_column: str,
    property_columns: Optional[List[str]] = None,
    batch_size: int = 1000,
):
    """
    Ingest nodes into Memgraph from a DataFrame.

    Args:
        db: Memgraph database connection
        df: DataFrame containing node data
        label: Node label (e.g., 'Account', 'User')
        id_column: Column name for node ID
        property_columns: Additional columns to include as properties
        batch_size: Number of nodes to insert per batch
    """
    property_columns = property_columns or []

    for i in range(0, len(df), batch_size):
        batch = df.iloc[i : i + batch_size]

        for _, row in batch.iterrows():
            node_id = row[id_column]

            # Build property string
            props = {"id": node_id}
            for col in property_columns:
                if col in row and pd.notna(row[col]):
                    props[col] = row[col]

            # Create Cypher property string
            prop_str = ", ".join([f"{k}: ${k}" for k in props.keys()])

            query = f"CREATE (n:{label} {{{prop_str}}})"
            db.query(query, props)

        print(f"Ingested {min(i + batch_size, len(df))} {label} nodes")


def ingest_relationships(
    db: Memgraph,
    df: pd.DataFrame,
    rel_type: str,
    from_label: str,
    from_column: str,
    to_label: str,
    to_column: str,
    property_columns: Optional[List[str]] = None,
    batch_size: int = 1000,
):
    """
    Ingest relationships into Memgraph from a DataFrame.

    Args:
        db: Memgraph database connection
        df: DataFrame containing relationship data
        rel_type: Relationship type (e.g., 'TRANSFERRED_TO')
        from_label: Label of source node
        from_column: Column with source node ID
        to_label: Label of target node
        to_column: Column with target node ID
        property_columns: Additional columns as relationship properties
        batch_size: Batch size for ingestion
    """
    property_columns = property_columns or []

    for i in range(0, len(df), batch_size):
        batch = df.iloc[i : i + batch_size]

        for _, row in batch.iterrows():
            from_id = row[from_column]
            to_id = row[to_column]

            # Build property string
            props = {}
            for col in property_columns:
                if col in row and pd.notna(row[col]):
                    props[col] = row[col]

            prop_clause = ""
            if props:
                prop_str = ", ".join([f"{k}: ${k}" for k in props.keys()])
                prop_clause = f" {{{prop_str}}}"

            query = f"""
            MATCH (a:{label} {{id: $from_id}}), (b:{to_label} {{id: $to_id}})
            CREATE (a)-[r:{rel_type}{prop_clause}]->(b)
            """

            params = {"from_id": from_id, "to_id": to_id, **props}
            db.query(query, params)

        print(f"Ingested {min(i + batch_size, len(df))} {rel_type} relationships")


def create_indexes(db: Memgraph, label: str, property_name: str = "id"):
    """
    Create index on a node property for faster lookups.

    Args:
        db: Memgraph database connection
        label: Node label
        property_name: Property to index
    """
    query = f"CREATE INDEX ON :{label}({property_name})"
    db.query(query)
    print(f"Created index on :{label}({property_name})")


def clear_graph(db: Memgraph):
    """Clear all nodes and relationships from the graph."""
    db.query("MATCH (n) DETACH DELETE n")
    print("Graph cleared")


def get_graph_stats(db: Memgraph) -> Dict:
    """
    Get basic statistics about the graph.

    Returns:
        Dictionary with node counts, relationship counts, etc.
    """
    node_count = db.query("MATCH (n) RETURN count(n) as count")[0]["count"]
    rel_count = db.query("MATCH ()-[r]->() RETURN count(r) as count")[0]["count"]

    # Get node labels
    labels_result = db.query(
        "CALL schema.node_type_properties() YIELD nodeType RETURN distinct nodeType as label"
    )
    labels = [r["label"] for r in labels_result]

    return {
        "node_count": node_count,
        "relationship_count": rel_count,
        "node_labels": labels,
    }
