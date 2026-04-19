"""
models/_base.py — shared Base import for all model submodules.
Section: System
Dependencies: database.Base
"""

try:
    from ..database import Base
except ImportError:
    from database import Base  # when run directly from backend/

__all__ = ["Base"]
