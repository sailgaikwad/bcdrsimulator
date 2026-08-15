"""
Simulation run, events, scoring, and investigation domain models.

These models drive the discrete-event simulation engine and the
score ledger system.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
import uuid

from app.models.enums import (
    SimulationStatus,
    EventType,
    ScoreCategory,
    RiskLevel,
)


def _new_id() -> str:
    return str(uuid.uuid4())


class SimulationRun(BaseModel):
    """
    A single simulation run record.

    Each run has a stored RNG seed for reproducibility.
    The decisions_json field stores the full decision history
    to enable counterfactual replay.
    """
    id: str = Field(default_factory=_new_id)
    org_id: str
    scenario_id: str
    rng_seed: int
    status: SimulationStatus = SimulationStatus.CREATED
    start_time: Optional[float] = None     # simulation clock
    end_time: Optional[float] = None
    total_downtime_hours: Optional[float] = None
    final_resilience_score: Optional[float] = None
    final_risk_level: Optional[RiskLevel] = None
    decisions_json: Optional[str] = None
    config_json: Optional[str] = None
    schema_version: str = Field(default="1.0")
    state_snapshot_json: Optional[str] = None
    event_ledger_json: Optional[str] = None
    timeline_json: Optional[str] = None
    team_id: Optional[str] = None          # future-ready

    model_config = {"frozen": False}


class SimulationEvent(BaseModel):
    """
    A discrete event in the simulation event queue.

    Events are ordered by (time, priority). Lower priority number
    means higher precedence for tie-breaking.
    """
    id: str = Field(default_factory=_new_id)
    run_id: str
    event_type: EventType
    time: float = Field(ge=0.0, description="Simulation clock time in hours")
    priority: int = Field(default=5, ge=0, le=10)
    system_id: Optional[str] = None
    description: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": False}

    def __lt__(self, other: "SimulationEvent") -> bool:
        """Enable heapq ordering: sort by time, then priority."""
        if self.time != other.time:
            return self.time < other.time
        return self.priority < other.priority


class ScoreEvent(BaseModel):
    """
    A single entry in the resilience score ledger.

    Every decision produces a ScoreEvent explaining what changed
    and why. This creates an explainable audit trail rather than
    a black-box final score.
    """
    id: str = Field(default_factory=_new_id)
    run_id: str
    decision_id: Optional[str] = None
    category: ScoreCategory
    delta: float
    reason: str
    event_time: float = Field(ge=0.0)

    model_config = {"frozen": False}


class HiddenFact(BaseModel):
    """
    A fact with true value hidden from the user until investigated.

    Models uncertainty: the user sees a range [revealed_low, revealed_high]
    and a confidence level. Spending time investigating narrows the range.

    Examples:
        backup_integrity: true=0.6, range=[0.0, 1.0], confidence=0.0
        After investigation: range=[0.4, 0.8], confidence=0.6
    """
    id: str = Field(default_factory=_new_id)
    run_id: str
    fact_key: str
    true_value: float
    revealed_low: Optional[float] = None
    revealed_high: Optional[float] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    investigated: bool = False

    model_config = {"frozen": False}

    def reveal_range(self, accuracy: float) -> tuple[float, float]:
        """
        Narrow the revealed range based on investigation accuracy.

        accuracy: 0.0–1.0, how close the revealed range gets to truth
        Returns the new (low, high) range.
        """
        full_low = self.revealed_low if self.revealed_low is not None else 0.0
        full_high = self.revealed_high if self.revealed_high is not None else 1.0

        # Narrow toward true value proportional to accuracy
        new_low = full_low + (self.true_value - full_low) * accuracy * 0.8
        new_high = full_high - (full_high - self.true_value) * accuracy * 0.8

        # Ensure range still contains true value
        new_low = min(new_low, self.true_value)
        new_high = max(new_high, self.true_value)

        self.revealed_low = new_low
        self.revealed_high = new_high
        self.confidence = min(1.0, self.confidence + accuracy * 0.3)
        self.investigated = True

        return (new_low, new_high)


class RiskAssessment(BaseModel):
    """
    A point-in-time risk assessment for a system.

    Risk = Probability × Impact × Exposure
    """
    id: str = Field(default_factory=_new_id)
    run_id: str
    system_id: Optional[str] = None
    assessment_time: Optional[float] = None
    probability: float = Field(ge=0.0, le=1.0)
    impact: float = Field(ge=0.0, le=1.0)
    exposure: float = Field(ge=0.0, le=1.0)
    risk_score: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    notes: Optional[str] = None

    model_config = {"frozen": False}

    def compute(self) -> float:
        """Calculate risk score = P × I × E and derive risk level."""
        self.risk_score = self.probability * self.impact * self.exposure
        self.risk_level = RiskLevel.from_score(self.risk_score)
        return self.risk_score


class ResourcePool(BaseModel):
    """
    Finite resource constraints for recovery operations.

    Prevents simultaneous recovery of everything — forces
    prioritization decisions.
    """
    team_capacity: int = Field(default=3, ge=1, description="Max parallel recovery actions")
    active_recoveries: int = Field(default=0, ge=0)
    budget_remaining: float = Field(default=100000.0, ge=0.0)
    backup_slots: int = Field(default=3, ge=0)
    infrastructure_capacity: int = Field(default=5, ge=1)

    model_config = {"frozen": False}

    def can_start_recovery(self, resource_cost: float, monetary_cost: float) -> bool:
        """Check if resources are available to start a new recovery."""
        return (
            self.active_recoveries < self.team_capacity
            and self.budget_remaining >= monetary_cost
        )

    def allocate(self, resource_cost: float, monetary_cost: float) -> None:
        """Consume resources for a recovery action."""
        self.active_recoveries += 1
        self.budget_remaining -= monetary_cost

    def release(self) -> None:
        """Free a recovery slot when an action completes."""
        self.active_recoveries = max(0, self.active_recoveries - 1)
