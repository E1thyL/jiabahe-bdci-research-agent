"""Conservative, serializable claim/evidence audit map."""
from dataclasses import dataclass, asdict
import json
from typing import Any
from .value_gate.schema import ScientificSupportLevel

@dataclass(frozen=True)
class ClaimLink:
    claim_id: str
    claim_type: str
    text: str
    evidence_ids: tuple[str, ...] = ()
    citations: tuple[str, ...] = ()
    minimum_support_level: ScientificSupportLevel | str = ScientificSupportLevel.FULL_TEXT
    technical_difference: str = ""
    limitation: str = ""

    def __post_init__(self):
        if not self.claim_id.strip() or not self.text.strip(): raise ValueError("claim_id and text must not be empty")
        object.__setattr__(self, "minimum_support_level", ScientificSupportLevel(self.minimum_support_level))

@dataclass(frozen=True)
class ClaimMap:
    claims: tuple[ClaimLink, ...] = ()
    def validate(self, evidence: Any, *, citations: set[str] | None = None) -> tuple[str, ...]:
        ids = set(evidence.ids if hasattr(evidence, "ids") and not callable(evidence.ids) else evidence.ids())
        errors=[]; seen=set(); citations = citations or set()
        for c in self.claims:
            if c.claim_id in seen: errors.append(f"duplicate claim_id: {c.claim_id}")
            seen.add(c.claim_id)
            if not c.evidence_ids: errors.append(f"claim has no evidence: {c.claim_id}")
            unknown=set(c.evidence_ids)-ids
            if unknown: errors.append(f"unknown evidence_id(s): {', '.join(sorted(unknown))}")
            if c.citations and citations and not set(c.citations)<=citations: errors.append(f"unknown citation for claim: {c.claim_id}")
            if not c.citations: errors.append(f"claim missing citation: {c.claim_id}")
        return tuple(errors)
    def to_dict(self):
        return {"claims":[{**asdict(c), "minimum_support_level": c.minimum_support_level.value} for c in self.claims]}
    def to_json(self): return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, indent=2)
    @classmethod
    def from_dict(cls, data):
        return cls(tuple(ClaimLink(**{**x, "evidence_ids":tuple(x.get("evidence_ids",())), "citations":tuple(x.get("citations",()))}) for x in data.get("claims",())))
    @classmethod
    def from_json(cls, value): return cls.from_dict(json.loads(value))
