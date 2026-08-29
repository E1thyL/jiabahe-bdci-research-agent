"""Offline-first literature source adapters."""

from .protocol import (
    LiteratureRecord,
    LiteratureSearchResult,
    LiteratureSearchStatus,
    LiteratureSourceAdapter,
)
from .replay import ReplayLiteratureSource
from .openalex import OpenAlexLiteratureSource
from .quality import LiteratureQualityFilter, LiteratureQualityReport
from .novelty import NoveltyGapBuilder, NoveltyGapReport

__all__ = [
    "LiteratureRecord",
    "LiteratureSearchResult",
    "LiteratureSearchStatus",
    "LiteratureSourceAdapter",
    "ReplayLiteratureSource",
    "OpenAlexLiteratureSource",
    "LiteratureQualityFilter",
    "LiteratureQualityReport",
    "NoveltyGapBuilder",
    "NoveltyGapReport",
]
