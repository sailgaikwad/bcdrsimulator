"""
Disaster scenario domain model.

Defines the structure of a disaster that can be applied to the simulation.
Scenarios are stored as JSON files and validated against a JSON Schema.
"""

from pydantic import BaseModel, Field
from typing import Optional
import uuid

from app.models.enums import DisasterCategory


def _new_id() -> str:
    return str(uuid.uuid4())


class AffectedSystem(BaseModel):
    """Specifies which system is hit and how severely."""
    system_id: str
    health_impact: float = Field(ge=0.0, le=1.0, description="Health reduction (1.0 = total failure)")
    delay_hours: float = Field(default=0.0, ge=0.0, description="Delay before this system is affected")


class DisasterScenario(BaseModel):
    """
    A disaster scenario definition.

    Contains the disaster type, severity, which systems are directly
    affected, and parameters for propagation and hidden facts.
    """
    id: str = Field(default_factory=_new_id)
    name: str
    category: DisasterCategory
    description: Optional[str] = None
    severity: float = Field(default=0.7, ge=0.0, le=1.0)
    affected_systems: list[AffectedSystem] = Field(default_factory=list)
    propagation_probability: float = Field(default=0.8, ge=0.0, le=1.0)

    # Hidden facts injected by this scenario (key → true value)
    # e.g., {"backup_integrity": 0.6, "corruption_pct": 0.35}
    hidden_facts: dict[str, float] = Field(default_factory=dict)

    model_config = {"frozen": False}
