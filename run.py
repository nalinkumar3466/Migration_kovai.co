#!/usr/bin/env python3
"""Entry point: python run.py"""

import sys
from pathlib import Path

# Allow running without pip install -e .
sys.path.insert(0, str(Path(__file__).parent / "src"))

from doc_analyzer.cli import main

if __name__ == "__main__":
    main()
