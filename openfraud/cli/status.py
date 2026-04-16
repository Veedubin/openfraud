"""CLI wrapper for OpenFraud status."""

import json
import sys
from pathlib import Path

import openfraud


def main():
    result = {
        "package": "openfraud",
        "version": getattr(openfraud, "__version__", "0.1.0"),
        "components": {
            "forensics": "available",
            "ml": "available",
            "graph": "available",
            "tui": "available",
        },
        "python": sys.version,
        "openfraud_path": str(Path(openfraud.__file__).parent),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
