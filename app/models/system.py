"""
Infrastructure system domain model.

Represents a single IT system/resource in the dependency graph —
servers, databases, firewalls, caches, etc.
"""

from pydantic import BaseModel, Field
from typing import Optional
import uuid

from app.models.enums import SystemType, SystemTier, SystemStatus


def _new_id() -> str:
    return str(uuid.uuid4())


class System(BaseModel):
    """
    An infrastructure component in the organization's topology.

    During simulation, health (0.0–1.0) and effective_availability
    are tracked dynamically. The base model stores static configuration.
    """
    id: str = Field(default_factory=_new_id)
    org_id: str
    name: str
    system_type: SystemType
    tier: SystemTier = SystemTier.STANDARD
    base_health: float = Field(default=1.0, ge=0.0, le=1.0)
    recovery_priority: int = Field(default=5, ge=1, le=10)

    model_config = {"frozen": False}


class SystemState(BaseModel):
    """
    Runtime state of a system during an active simulation.

    Tracks current health, effective availability (accounting for
    dependency propagation), and timing of failure/recovery.

    This is a transient object — not persisted directly, but
    reconstructed from event logs for replay.
    """
    system_id: str
    health: float = Field(default=1.0, ge=0.0, le=1.0)
    status: SystemStatus = SystemStatus.OPERATIONAL
    effective_availability: float = Field(default=1.0, ge=0.0, le=1.0)
    failed_at: Optional[float] = None
    restored_at: Optional[float] = None

    model_config = {"frozen": False}

    def apply_damage(self, damage: float, time: float) -> None:
        """Reduce health by damage amount, clamped to [0.0, 1.0]."""
        self.health = max(0.0, self.health - damage)
        if self.health == 0.0:
            self.status = SystemStatus.FAILED
            if self.failed_at is None:
                self.failed_at = time
        elif self.health < 1.0:
            self.status = SystemStatus.DEGRADED
            if self.failed_at is None:
                self.failed_at = time

    def apply_recovery(self, restored_health: float, time: float) -> None:
        """Increase health from recovery, clamped to [0.0, 1.0]."""
        self.health = min(1.0, self.health + restored_health)
        if self.health >= 1.0:
            self.status = SystemStatus.RESTORED
            self.restored_at = time
        elif self.health > 0.0:
            self.status = SystemStatus.RECOVERING

    @property
    def is_operational(self) -> bool:
        return self.status in (SystemStatus.OPERATIONAL, SystemStatus.RESTORED)

    @property
    def is_down(self) -> bool:
        return self.status == SystemStatus.FAILED
