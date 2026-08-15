"""
Dependency edge model for the infrastructure graph.

A dependency represents a directed edge from source → target,
meaning 'target depends on source' (source provides to target).
"""

from pydantic import BaseModel, Field
from typing import Optional
import uuid

from app.models.enums import DependencyType


def _new_id() -> str:
    return str(uuid.uuid4())


class Dependency(BaseModel):
    """
    A directed dependency edge in the infrastructure graph.

    Direction convention: source_id → target_id
        meaning target_id depends on source_id.
        If source fails, target is affected.

    Attributes:
        dep_type: HARD or SOFT
            HARD — target cannot function without source
            SOFT — target degrades without source but continues
        weight: Strength of coupling (0.0–1.0)
            1.0 = full dependency
            0.3 = partial dependency
        description: Human-readable explanation of why this dependency exists
    """
    id: str = Field(default_factory=_new_id)
    org_id: str
    source_id: str
    target_id: str
    dep_type: DependencyType = DependencyType.HARD
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    description: Optional[str] = None

    model_config = {"frozen": False}
