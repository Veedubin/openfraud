"""CLI wrapper for OpenFraud graph analysis."""

import argparse
import json

import pandas as pd
from memgraph_toolbox.api.memgraph import Memgraph

from openfraud.graph.network_analysis import (
    calculate_pagerank,
    detect_communities,
    find_self_loops,
    find_spiderweb_patterns,
    find_cliques,
    get_network_metrics,
)


def main():
    parser = argparse.ArgumentParser(description="OpenFraud Graph CLI")
    parser.add_argument(
        "--analysis",
        required=True,
        choices=[
            "pagerank",
            "communities",
            "self_loops",
            "spiderwebs",
            "cliques",
            "metrics",
        ],
    )
    parser.add_argument(
        "--memgraph-url",
        default="bolt://openfraud_memgraph:7687",
    )
    args = parser.parse_args()

    db = Memgraph(url=args.memgraph_url)

    if args.analysis == "pagerank":
        df = calculate_pagerank(db)
    elif args.analysis == "communities":
        df = detect_communities(db)
    elif args.analysis == "self_loops":
        df = find_self_loops(db)
    elif args.analysis == "spiderwebs":
        df = find_spiderweb_patterns(db)
    elif args.analysis == "cliques":
        df = find_cliques(db)
    elif args.analysis == "metrics":
        metrics = get_network_metrics(db)
        print(json.dumps(metrics, indent=2, default=str))
        return

    records = df.head(100).where(pd.notnull(df), None).to_dict(orient="records")
    print(json.dumps(records, indent=2, default=str))


if __name__ == "__main__":
    main()
