"""
schemas_common.py — Reusable Pydantic string constraints.

Section: System
Dependencies: pydantic

All types auto-strip whitespace AND enforce `max_length`. Over-length input
raises `RequestValidationError` → HTTP 422 (handled in main.py with a
child-friendly JSON shape). Replaces the previous `self.x = self.x.strip()[:N]`
pattern which silently truncated data.
"""
from __future__ import annotations

from typing import Annotated

from pydantic import StringConstraints

# Short identifiers / labels
Str20   = Annotated[str, StringConstraints(strip_whitespace=True, max_length=20)]
Str30   = Annotated[str, StringConstraints(strip_whitespace=True, max_length=30)]
Str50   = Annotated[str, StringConstraints(strip_whitespace=True, max_length=50)]
Str80   = Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)]
Str100  = Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]
Str120  = Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)]
Str200  = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]
Str300  = Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)]
Str500  = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]

# Longer user-write bodies
Str1000  = Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)]
Str5000  = Annotated[str, StringConstraints(strip_whitespace=True, max_length=5000)]
Str10000 = Annotated[str, StringConstraints(strip_whitespace=True, max_length=10000)]
