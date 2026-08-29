"""Offline-first literature source adapters."""

from .protocol import (
    LiteratureRecord,
    LiteratureSearchResult,
    LiteratureSearchStatus,
    LiteratureSourceAdapter,
)
from .replay import ReplayLiteratureSource
from .openalex import OpenAlexLiteratureSource

__all__ = [
    "LiteratureRecord",
    "LiteratureSearchResult",
    "LiteratureSearchStatus",
    "LiteratureSourceAdapter",
    "ReplayLiteratureSource",
    "OpenAlexLiteratureSource",
]
