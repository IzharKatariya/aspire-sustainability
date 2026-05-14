"""
conftest.py
────────────
Tells pytest and Python that the project root is the base
for all imports. This makes 'from app.core.x import y' work
from anywhere in the project.
"""

import sys
from pathlib import Path
import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "live: marks tests that make real API calls (slow, deselect with -m 'not live')"
    )

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))