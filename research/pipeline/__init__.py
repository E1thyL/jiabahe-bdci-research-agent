"""Stage-oriented research pipeline."""

from .runner import PipelineResult, ResearchPipelineRunner
from .experiment_stages import (
    ExperimentExecutionArtifact,
    ExperimentExecutionStage,
    ResultAnalysisArtifact,
    ResultAnalysisStage,
)
from .g3 import DraftingReadiness, check_drafting_readiness

__all__ = [
    "ExperimentExecutionArtifact", "ExperimentExecutionStage",
    "PipelineResult", "ResearchPipelineRunner",
    "ResultAnalysisArtifact", "ResultAnalysisStage",
    "DraftingReadiness", "check_drafting_readiness",
]
