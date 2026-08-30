"""Single-source OpenAlex literature adapter.

The default transport uses the public OpenAlex API. Tests inject a transport
callable, so all adapter behavior remains deterministic and offline-testable.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..value_gate.schema import CandidateProblem, EvidenceStatus, ScientificSupportLevel
from .protocol import (
    LiteratureRecord,
    LiteratureSearchResult,
    LiteratureSearchStatus,
)

Transport = Callable[[str, float], tuple[int, bytes]]


class OpenAlexLiteratureSource:
    """Search OpenAlex with bounded pagination, retries, and raw snapshots."""

    API_URL = "https://api.openalex.org/works"
    source_name = "openalex"

    def __init__(
        self,
        *,
        cache_dir: str | Path,
        research_run_id: str,
        timeout: float = 10.0,
        max_pages: int = 1,
        max_retries: int = 2,
        request_fn: Transport | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        artifact_path_resolver: Callable[[Path], str] | None = None,
    ) -> None:
        if not research_run_id.strip():
            raise ValueError("research_run_id must not be empty")
        if timeout <= 0 or max_pages < 1 or max_retries < 0:
            raise ValueError("timeout must be positive; page and retry limits must be valid")
        self.cache_dir = Path(cache_dir)
        self.research_run_id = research_run_id
        self.timeout = timeout
        self.max_pages = max_pages
        self.max_retries = max_retries
        self._request = request_fn or _request_openalex
        self._sleep = sleep_fn
        self._artifact_path_resolver = artifact_path_resolver
        self._usage_request_count = 0
        self._usage_retry_count = 0
        self._usage_started = 0.0

    @property
    def usage_measurement(self) -> dict[str, int]:
        """Return transport measurements without exposing response contents."""
        elapsed = int((time.monotonic() - self._usage_started) * 1000) if self._usage_started else 0
        return {
            "request_count": self._usage_request_count,
            "retry_count": self._usage_retry_count,
            "wall_time_ms": elapsed,
        }

    def search(
        self,
        candidate: CandidateProblem,
        topic_config: dict[str, Any] | None = None,
    ) -> LiteratureSearchResult:
        self._usage_started = time.monotonic()
        self._usage_request_count = 0
        self._usage_retry_count = 0
        config = topic_config or {}
        query = str(config.get("query") or candidate.problem_statement).strip()
        cache_path = self._cache_path(query or "empty-query")
        if not query:
            snapshot = {"query": query, "source_name": self.source_name, "status": "empty", "results": []}
            self._write_snapshot(cache_path, snapshot)
            return self._result(candidate, query, LiteratureSearchStatus.EMPTY, artifact_path=self._artifact_reference(cache_path), raw_response=snapshot)
        per_page = min(max(int(config.get("per_page", 25)), 1), 100)
        if cache_path.exists():
            try:
                payload = json.loads(cache_path.read_text(encoding="utf-8"))
                return self._result_from_payload(candidate, query, payload, cache_path)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                return self._result(
                    candidate, query, LiteratureSearchStatus.FAILED,
                    failure_reason=f"invalid cached OpenAlex response: {exc}",
                    artifact_path=self._artifact_reference(cache_path),
                )

        all_records: list[dict[str, Any]] = []
        for page in range(1, self.max_pages + 1):
            params = urlencode({"search": query, "per-page": per_page, "page": page})
            status, body, failure = self._request_with_retries(f"{self.API_URL}?{params}")
            if failure is not None:
                self._write_failure(cache_path, query, failure)
                return self._result(
                    candidate, query, LiteratureSearchStatus.FAILED,
                    failure_reason=failure, artifact_path=self._artifact_reference(cache_path),
                )
            try:
                payload = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                self._write_failure(cache_path, query, f"invalid OpenAlex JSON: {exc}")
                return self._result(
                    candidate, query, LiteratureSearchStatus.FAILED,
                    failure_reason=f"invalid OpenAlex JSON: {exc}", artifact_path=self._artifact_reference(cache_path),
                )
            if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
                self._write_failure(cache_path, query, "OpenAlex response lacks a results list")
                return self._result(
                    candidate, query, LiteratureSearchStatus.FAILED,
                    failure_reason="OpenAlex response lacks a results list", artifact_path=self._artifact_reference(cache_path),
                )
            all_records.extend(payload["results"])
            if len(payload["results"]) < per_page:
                break

        snapshot = {
            "query": query,
            "source_name": "openalex",
            "results": all_records,
        }
        self._write_snapshot(cache_path, snapshot)
        return self._result_from_payload(candidate, query, snapshot, cache_path)

    def _artifact_reference(self, path: Path) -> str:
        if self._artifact_path_resolver is not None:
            return self._artifact_path_resolver(path)
        if path.is_absolute():
            try:
                return path.relative_to(Path.cwd()).as_posix()
            except ValueError:
                return path.as_posix()
        return path.as_posix()

    @staticmethod
    def _write_snapshot(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")

    def _write_failure(self, path: Path, query: str, reason: str) -> None:
        self._write_snapshot(path, {
            "query": query, "source_name": self.source_name, "status": "failed",
            "failure_reason": reason, "results": [],
        })

    def _request_with_retries(self, url: str) -> tuple[int, bytes, str | None]:
        for attempt in range(self.max_retries + 1):
            self._usage_request_count += 1
            try:
                status, body = self._request(url, self.timeout)
                if status == 200:
                    return status, body, None
                failure = f"OpenAlex HTTP {status}"
                retryable = status == 429 or status >= 500
            except (HTTPError, URLError, TimeoutError, OSError) as exc:
                failure = f"OpenAlex request failed: {exc}"
                retryable = True
            if not retryable or attempt == self.max_retries:
                return 0, b"", failure
            self._usage_retry_count += 1
            self._sleep(0.1 * (2**attempt))
        return 0, b"", "OpenAlex retry limit exhausted"

    def _cache_path(self, query: str) -> Path:
        query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]
        return self.cache_dir / self.research_run_id / f"openalex-{query_hash}.json"

    def _result_from_payload(
        self,
        candidate: CandidateProblem,
        query: str,
        payload: dict[str, Any],
        cache_path: Path,
    ) -> LiteratureSearchResult:
        records: list[LiteratureRecord] = []
        skipped = False
        for raw in payload.get("results", []):
            record = _normalize_record(raw)
            if record is None:
                skipped = True
            else:
                records.append(record)
        if not records:
            status = LiteratureSearchStatus.EMPTY if not skipped else LiteratureSearchStatus.PARTIAL
        else:
            status = LiteratureSearchStatus.PARTIAL if skipped else LiteratureSearchStatus.SUCCESS
        return self._result(
            candidate, query, status, records=tuple(records), artifact_path=self._artifact_reference(cache_path),
            raw_response=payload,
        )

    def _result(self, candidate: CandidateProblem, query: str, status: LiteratureSearchStatus,
                *, records: tuple[LiteratureRecord, ...] = (), failure_reason: str | None = None,
                artifact_path: str | None = None, raw_response: dict[str, Any] | None = None) -> LiteratureSearchResult:
        return LiteratureSearchResult(
            candidate_problem=candidate.problem_statement,
            query=query,
            source_name="openalex",
            records=records,
            status=status,
            failure_reason=failure_reason,
            artifact_path=artifact_path,
            raw_response=raw_response,
        )


def _request_openalex(url: str, timeout: float) -> tuple[int, bytes]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "bdci-research-agent/0.1"})
    with urlopen(request, timeout=timeout) as response:
        return int(response.status), response.read()


def _normalize_record(raw: Any) -> LiteratureRecord | None:
    if not isinstance(raw, dict):
        return None
    location = raw.get("primary_location") or {}
    source_uri = (
        location.get("landing_page_url")
        or raw.get("doi")
        or raw.get("id")
    )
    title = str(raw.get("title") or "").strip()
    excerpt = _abstract_text(raw.get("abstract_inverted_index"))
    if not source_uri or not title or not excerpt:
        return None
    authors = tuple(
        str((author.get("author") or {}).get("display_name") or "").strip()
        for author in raw.get("authorships", [])
        if isinstance(author, dict) and (author.get("author") or {}).get("display_name")
    )
    return LiteratureRecord(
        source_uri=str(source_uri),
        title=title,
        authors=authors,
        year=int(raw.get("publication_year") or 0),
        venue=str((location.get("source") or {}).get("display_name") or ""),
        excerpt=excerpt,
        evidence_type="prior_work",
        verification_status=EvidenceStatus.VERIFIED,
        support_level=ScientificSupportLevel.ABSTRACT,
    )


def _abstract_text(index: Any) -> str:
    if not isinstance(index, dict):
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in index.items():
        if isinstance(positions, list):
            words.extend((int(position), str(word)) for position in positions)
    return " ".join(word for _, word in sorted(words))
