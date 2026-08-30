"""Injectable in-memory artifact registry for offline pipeline runs."""
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Artifact:
    path: str
    research_run_id: str
    artifact_type: str
    content: Any

class ArtifactStore:
    def __init__(self): self._items: dict[str, Artifact] = {}
    def register(self, *, path: str, research_run_id: str, artifact_type: str, content: Any) -> Artifact:
        item = Artifact(path, research_run_id, artifact_type, content)
        self._items[path] = item
        return item
    def resolve(self, path: str) -> Artifact | None: return self._items.get(path)
