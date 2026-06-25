"""Shared pytest fixtures and import path setup for the test suite.

The ``scripts/`` directory is not an installable package, so add it to
``sys.path`` here (once, before collection) to keep individual test modules free
of import-order boilerplate.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
