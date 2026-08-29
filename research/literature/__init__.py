"""Offline-first literature source adapters."""

from .protocol import (
    LiteratureRecord,
    LiteratureSearchResult,
    LiteratureSearchStatus,
    LiteratureSourceAdapter,
)
from .replay import ReplayLiteratureSource

__all__ = [
    "LiteratureRecord",
    "LiteratureSearchResult",
    "LiteratureSearchStatus",
    "LiteratureSourceAdapter",
    "ReplayLiteratureSource",
]
