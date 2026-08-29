"""Deterministic offline replay literature adapter."""

from __future__ import annotations

from typing import Any

from ..value_gate.schema import CandidateProblem
from .protocol import (
    LiteratureRecord,
    LiteratureSearchResult,
    LiteratureSearchStatus,
)


class ReplayLiteratureSource:
    """Return fixed records for fixture queries without network access."""

    def __init__(
        self,
        fixtures: dict[str, tuple[LiteratureRecord, ...]],
        *,
        failures: dict[str, str] | None = None,
        source_name: str = "replay",
    ) -> None:
        self._fixtures = fixtures
        self._failures = failures or {}
        self._source_name = source_name

    def search(
        self,
        candidate: CandidateProblem,
        topic_config: dict[str, Any] | None = None,
    ) -> LiteratureSearchResult:
        config = topic_config or {}
        query = str(config.get("query") or candidate.problem_statement).strip()
        if query in self._failures:
            return LiteratureSearchResult(
                candidate_problem=candidate.problem_statement,
                query=query,
                source_name=self._source_name,
                status=LiteratureSearchStatus.FAILED,
                failure_reason=self._failures[query],
            )
        records = self._fixtures.get(query)
        if records is None:
            return LiteratureSearchResult(
                candidate_problem=candidate.problem_statement,
                query=query,
                source_name=self._source_name,
                status=LiteratureSearchStatus.EMPTY,
            )
        return LiteratureSearchResult(
            candidate_problem=candidate.problem_statement,
            query=query,
            source_name=self._source_name,
            records=records,
            status=(
                LiteratureSearchStatus.SUCCESS
                if records
                else LiteratureSearchStatus.EMPTY
            ),
        )
