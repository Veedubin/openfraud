"""
openfraud/graph/network_analysis.py
Graph algorithms for fraud detection.
"""

import pandas as pd
from typing import Dict, List, Optional
from memgraph_toolbox.api.memgraph import Memgraph


def calculate_pagerank(db: Memgraph) -> pd.DataFrame:
    """
    Calculate PageRank centrality for all nodes.

    High PageRank indicates influential/hub nodes.

    Returns:
        DataFrame with node id, label, and pagerank score
    """
    query = """
    CALL pagerank.get()
    YIELD node, rank
    RETURN node.id as node_id, labels(node)[0] as label, rank as pagerank
    ORDER BY rank DESC
    """
    result = db.query(query)
    return pd.DataFrame(result)


def detect_communities(db: Memgraph) -> pd.DataFrame:
    """
    Detect communities using Louvain algorithm.

    Returns:
        DataFrame with node id and community assignment
    """
    query = """
    CALL community_detection.get()
    YIELD node, community_id
    RETURN node.id as node_id, community_id
    ORDER BY community_id
    """
    result = db.query(query)
    return pd.DataFrame(result)


def find_self_loops(db: Memgraph, rel_type: Optional[str] = None) -> pd.DataFrame:
    """
    Find nodes with relationships to themselves.

    Args:
        rel_type: Optional relationship type filter

    Returns:
        DataFrame with self-looping node IDs
    """
    rel_filter = f":{rel_type}" if rel_type else ""
    query = f"""
    MATCH (n)-[r{rel_filter}]->(n)
    RETURN n.id as node_id, type(r) as relationship_type
    """
    result = db.query(query)
    return pd.DataFrame(result)


def find_spiderweb_patterns(
    db: Memgraph, min_connections: int = 10, center_label: Optional[str] = None
) -> pd.DataFrame:
    """
    Find nodes with many connections but few interconnections between leaves.
    Pattern of a hub-and-spoke network.

    Args:
        db: Memgraph connection
        min_connections: Minimum connections to be considered a hub
        center_label: Optional filter for center node label

    Returns:
        DataFrame with hub nodes and connection counts
    """
    label_filter = f"WHERE center:{center_label}" if center_label else ""

    query = f"""
    MATCH (center)-[r]-(leaf)
    {label_filter}
    WITH center, count(DISTINCT leaf) as connections
    WHERE connections >= {min_connections}
    RETURN center.id as hub_id, labels(center)[0] as hub_type, connections
    ORDER BY connections DESC
    """
    result = db.query(query)
    return pd.DataFrame(result)


def find_cliques(db: Memgraph, min_size: int = 3) -> pd.DataFrame:
    """
    Find cliques (fully connected subgraphs).

    Args:
        db: Memgraph connection
        min_size: Minimum clique size

    Returns:
        DataFrame with clique members
    """
    # Triangle detection (3-clique)
    if min_size == 3:
        query = """
        MATCH (a)-[:RELATES_TO]-(b)-[:RELATES_TO]-(c)-[:RELATES_TO]-(a)
        WHERE a.id < b.id AND b.id < c.id
        RETURN a.id as node_1, b.id as node_2, c.id as node_3
        """
    else:
        # For larger cliques, use community detection as approximation
        query = f"""
        CALL community_detection.get()
        YIELD node, community_id
        WITH community_id, collect(node.id) as members
        WHERE size(members) >= {min_size}
        RETURN community_id, members
        """

    result = db.query(query)
    return pd.DataFrame(result)


def get_node_neighborhood(db: Memgraph, node_id: str, max_distance: int = 2) -> pd.DataFrame:
    """
    Get all nodes within a certain distance of a target node.

    Args:
        db: Memgraph connection
        node_id: Center node ID
        max_distance: Maximum path length

    Returns:
        DataFrame with neighboring nodes and distances
    """
    query = f"""
    MATCH path = (center {{id: '{node_id}'}})-[*1..{max_distance}]-(neighbor)
    RETURN DISTINCT 
        neighbor.id as neighbor_id,
        labels(neighbor)[0] as neighbor_type,
        min(length(path)) as distance
    ORDER BY distance
    """
    result = db.query(query)
    return pd.DataFrame(result)


def analyze_community_fraud_rate(db: Memgraph, fraud_node_label: str = "Account") -> pd.DataFrame:
    """
    Calculate fraud rate per community.

    Args:
        db: Memgraph connection
        fraud_node_label: Node label with fraud indicator

    Returns:
        DataFrame with community fraud statistics
    """
    query = f"""
    MATCH (n:{fraud_node_label})
    WHERE n.is_fraud IS NOT NULL
    WITH n.community_id as community, 
         count(n) as total,
         sum(CASE WHEN n.is_fraud = true THEN 1 ELSE 0 END) as fraud_count
    RETURN 
        community,
        total as community_size,
        fraud_count,
        fraud_count * 1.0 / total as fraud_rate
    ORDER BY fraud_rate DESC
    """
    result = db.query(query)
    return pd.DataFrame(result)


def get_network_metrics(db: Memgraph) -> Dict:
    """
    Get overall network statistics.

    Returns:
        Dictionary with network metrics
    """
    # Density
    density_query = """
    MATCH (n)
    WITH count(n) as node_count
    MATCH ()-[r]->()
    WITH node_count, count(r) as rel_count
    RETURN rel_count * 1.0 / (node_count * (node_count - 1)) as density
    """
    density_result = db.query(density_query)
    density = density_result[0]["density"] if density_result else 0

    # Average degree
    degree_query = """
    MATCH (n)-[r]-()
    RETURN avg(count(r)) as avg_degree
    """
    degree_result = db.query(degree_query)
    avg_degree = degree_result[0]["avg_degree"] if degree_result else 0

    return {
        "density": density,
        "average_degree": avg_degree,
    }
