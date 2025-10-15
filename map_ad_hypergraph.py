#!/usr/bin/env python3
"""
AD Hypergraph Repository Mapper CLI
==================================

Command-line interface for mapping AD hypergraph across all target repositories.
"""

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.tools.ad_hypergraph_repo_mapper import ADHypergraphRepoMapper, main

if __name__ == "__main__":
    main()