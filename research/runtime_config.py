"""Runtime policy for online literature and the official model channel."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import os
from typing import Any, Protocol


class LiteratureMode(StrEnum):
    OFFLINE = "offline"
    ONLINE_ALLOWLIST = "online_allowlist"
    AUTO = "auto"


@dataclass(frozen=True)
class ResearchRuntimeConfig:
    """Explicitly selects online, offline, or fallback literature behavior."""

    literature_mode: LiteratureMode | str = LiteratureMode.AUTO
    online_sources: tuple[str, ...] = ("openalex", "arxiv")

    def __post_init__(self) -> None:
        object.__setattr__(self, "literature_mode", LiteratureMode(self.literature_mode))
        allowed = tuple(dict.fromkeys(source.strip().lower() for source in self.online_sources if source.strip()))
        if not allowed:
            raise ValueError("online_sources must not be empty")
        unknown = set(allowed) - {"openalex", "arxiv"}
        if unknown:
            raise ValueError(f"online source not allowlisted: {sorted(unknown)}")
        object.__setattr__(self, "online_sources", allowed)

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> "ResearchRuntimeConfig":
        values = os.environ if environ is None else environ
        mode = values.get("LITERATURE_MODE", LiteratureMode.AUTO.value).strip().lower()
        sources = tuple(item for item in values.get("LITERATURE_ONLINE_SOURCES", "openalex,arxiv").split(",") if item.strip())
        return cls(mode, sources)


class OfficialDeepSeekClient(Protocol):
    """Injection boundary for the official DeepSeek V4 Flash client.

    The repository defines no transport implementation. Production wiring must
    provide the official endpoint and explicit usage measurements.
    """

    model: str

    def generate(self, prompt: str, **kwargs: Any) -> str:
        ...
