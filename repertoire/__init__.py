"""Repertoire - Classical music manager with AI-powered metadata enrichment."""
from __future__ import annotations

import sys
from pathlib import Path
import warnings

# Ensure bundled third-party dependencies (installed under ./vendor) are importable.
_VENDOR_PATH = Path(__file__).resolve().parent.parent / "vendor"

if _VENDOR_PATH.exists():
    vendor_str = str(_VENDOR_PATH)
    if vendor_str not in sys.path:
        sys.path.insert(0, vendor_str)

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None  # type: ignore

if load_dotenv:
    load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

__version__ = "0.1.0"
__all__ = ["__version__"]
