"""
Recovery strategy and plan domain models.

Recovery strategies define HOW a system can be recovered.
Recovery plans bind a strategy to a specific system during a simulation run.
"""

from pydantic import BaseModel, Field
from typing import Optional
import uuid

from app.models.enums import StrategyType


def _new_id() -> str:
    return str(uuid.uuid4())


class RecoveryStrategy(BaseModel):
    """
    A recovery strategy template.

    Time estimates use optimistic/likely/pessimistic values for
    PERT/triangular distribution sampling during simulation.

    Attributes:
        resource_cost: Team-hours or resource units consumed
        data_loss_hours: RPO impact — hours of data that may be lost
        monetary_cost: Simulated recovery cost (not real billing)
        risk_reduction: How much this strategy reduces ongoing risk (0.0–1.0)
    """
    id: str = Field(default_factory=_new_id)
    name: str
    strategy_type: StrategyType
    optimistic_hours: float = Field(ge=0.0)
    likely_hours: float = Field(ge=0.0)
    pessimistic_hours: float = Field(ge=0.0)
    resource_cost: float = Field(default=1.0, ge=0.0)
    data_loss_hours: float = Field(default=0.0, ge=0.0)
    monetary_cost: float = Field(default=0.0, ge=0.0)
    risk_reduction: float = Field(default=0.0, ge=0.0, le=1.0)
    description: Optional[str] = None

    model_config = {"frozen": False}


class RecoveryPlan(BaseModel):
    """
    A bound recovery action: a strategy applied to a specific system
    during a specific simulation run.
    """
    id: str = Field(default_factory=_new_id)
    run_id: str
    system_id: str
    strategy_id: str
    decision_time: Optional[float] = None
    start_time: Optional[float] = None
    completion_time: Optional[float] = None
    planned_duration: Optional[float] = None
    actual_duration: Optional[float] = None
    health_restored: float = Field(default=1.0, ge=0.0, le=1.0)
    resources_used: float = Field(default=0.0, ge=0.0)
    cost: float = Field(default=0.0, ge=0.0)
    success: bool = True

    model_config = {"frozen": False}
