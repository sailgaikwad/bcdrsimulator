"""
Business Impact Analysis (BIA) engine.

Tracks business-level impact during a simulation:
- Revenue loss accumulation
- SLA penalty accumulation
- Reputation decay
- Regulatory notification deadlines
- MTPD breach detection → business-failure state
- WRT (Work Recovery Time) tracking

Per spec §5 and §18.
"""

from dataclasses import dataclass, field
from typing import Optional

from app.models.organization import BusinessService
from app.models.system import SystemState
from app.models.enums import ScoreCategory
from app.core.scoring import ScoringEngine


@dataclass
class ServiceImpact:
    """Tracks cumulative business impact for one service during a simulation."""
    service_id: str
    service_name: str
    criticality: int
    rto_hours: float
    rpo_hours: float
    mtpd_hours: float

    # Cumulative impact
    downtime_hours: float = 0.0
    revenue_lost: float = 0.0
    sla_penalties: float = 0.0
    reputation_damage: float = 0.0

    # State flags
    rto_breached: bool = False
    rpo_breached: bool = False
    mtpd_breached: bool = False
    service_failed_at: Optional[float] = None
    service_restored_at: Optional[float] = None

    # WRT — Work Recovery Time tracking
    # Technical recovery != business recovery (backlog clearing)
    technical_recovery_time: Optional[float] = None
    business_recovery_time: Optional[float] = None
    wrt_hours: float = 0.0  # Difference between business and technical recovery

    # Current effective availability (from supporting systems)
    current_availability: float = 1.0


class BIAEngine:
    """
    Tracks business impact analysis during simulation.

    Monitors all business services and their dependency on infrastructure
    systems. When systems degrade/fail, business services are impacted
    proportionally.

    Key capabilities:
    - Revenue loss tracking
    - SLA penalty accumulation
    - Reputation decay
    - MTPD breach → business-failure state
    - WRT (Work Recovery Time) as gap between technical and business recovery
    """

    def __init__(self, run_id: str, scoring: ScoringEngine):
        self.run_id = run_id
        self._scoring = scoring
        self._impacts: dict[str, ServiceImpact] = {}
        self._service_system_map: dict[str, list[str]] = {}  # service_id → system_ids

    def register_service(
        self,
        service: BusinessService,
        supporting_system_ids: list[str],
    ) -> None:
        """Register a business service and its supporting systems."""
        self._impacts[service.id] = ServiceImpact(
            service_id=service.id,
            service_name=service.name,
            criticality=service.criticality,
            rto_hours=service.rto_hours or 4.0,
            rpo_hours=service.rpo_hours or 1.0,
            mtpd_hours=service.mtpd_hours or 24.0,
        )
        self._service_system_map[service.id] = supporting_system_ids

    def update_service_availability(
        self,
        service_id: str,
        system_states: dict[str, SystemState],
        current_time: float,
        dt_hours: float = 0.0,
    ) -> Optional[ServiceImpact]:
        """
        Update a service's availability based on its supporting systems' states.

        Returns the updated ServiceImpact or None if service not registered.
        """
        impact = self._impacts.get(service_id)
        if impact is None:
            return None

        system_ids = self._service_system_map.get(service_id, [])
        if not system_ids:
            return impact

        # Service availability = worst-case of supporting systems
        availabilities = []
        for sys_id in system_ids:
            state = system_states.get(sys_id)
            if state is not None:
                availabilities.append(state.effective_availability)

        if availabilities:
            impact.current_availability = min(availabilities)
        else:
            impact.current_availability = 1.0

        return impact

    def accumulate_impact(
        self,
        service: BusinessService,
        impact: ServiceImpact,
        current_time: float,
        dt_hours: float,
    ) -> list[str]:
        """
        Accumulate business impact for a time interval.

        Returns list of triggered events (e.g., "rto_breached", "mtpd_breached").
        """
        triggered = []

        if impact.current_availability >= 1.0:
            return triggered

        # Track when service first went down
        if impact.service_failed_at is None and impact.current_availability < 0.5:
            impact.service_failed_at = current_time

        # Accumulate downtime (weighted by unavailability)
        unavailability = 1.0 - impact.current_availability
        impact.downtime_hours += dt_hours * unavailability

        # Revenue loss
        revenue_rate = service.revenue_per_hour or 0.0
        revenue_loss = revenue_rate * dt_hours * unavailability
        impact.revenue_lost += revenue_loss

        # SLA penalties
        sla_rate = service.sla_penalty_per_hour or 0.0
        sla_loss = sla_rate * dt_hours * unavailability
        impact.sla_penalties += sla_loss

        # Reputation decay (compounds)
        rep_rate = service.reputation_decay_rate or 0.0
        impact.reputation_damage += rep_rate * dt_hours * unavailability

        # Check RTO breach
        if not impact.rto_breached and impact.downtime_hours > impact.rto_hours:
            impact.rto_breached = True
            triggered.append("rto_breached")
            self._scoring.record(
                category=ScoreCategory.RECOVERY_PERFORMANCE,
                delta=-15.0,
                reason=(
                    f"RTO breached for {impact.service_name}: "
                    f"downtime {impact.downtime_hours:.1f}h exceeds "
                    f"target {impact.rto_hours:.1f}h"
                ),
                event_time=current_time,
            )

        # Check MTPD breach → business-failure state
        if not impact.mtpd_breached and impact.downtime_hours > impact.mtpd_hours:
            impact.mtpd_breached = True
            triggered.append("mtpd_breached")
            self._scoring.record(
                category=ScoreCategory.BUSINESS_AVAILABILITY,
                delta=-30.0,
                reason=(
                    f"CRITICAL: MTPD breached for {impact.service_name}. "
                    f"Downtime {impact.downtime_hours:.1f}h exceeds "
                    f"maximum tolerable {impact.mtpd_hours:.1f}h. "
                    f"Business failure state triggered."
                ),
                event_time=current_time,
            )

        return triggered

    def record_technical_recovery(
        self,
        service_id: str,
        recovery_time: float,
    ) -> None:
        """Record when a service's systems are technically recovered."""
        impact = self._impacts.get(service_id)
        if impact is None:
            return
        impact.technical_recovery_time = recovery_time
        impact.service_restored_at = recovery_time

    def record_business_recovery(
        self,
        service_id: str,
        recovery_time: float,
    ) -> None:
        """
        Record when business operations are fully recovered (backlog cleared).

        WRT = business_recovery_time - technical_recovery_time
        """
        impact = self._impacts.get(service_id)
        if impact is None:
            return
        impact.business_recovery_time = recovery_time

        if impact.technical_recovery_time is not None:
            impact.wrt_hours = recovery_time - impact.technical_recovery_time

    def check_rpo(
        self,
        service_id: str,
        actual_data_loss_hours: float,
        current_time: float,
    ) -> bool:
        """
        Check if RPO is breached for a service.

        Returns True if RPO is breached.
        """
        impact = self._impacts.get(service_id)
        if impact is None:
            return False

        if actual_data_loss_hours > impact.rpo_hours:
            if not impact.rpo_breached:
                impact.rpo_breached = True
                self._scoring.record(
                    category=ScoreCategory.DATA_PROTECTION,
                    delta=-20.0,
                    reason=(
                        f"RPO breached for {impact.service_name}: "
                        f"data loss {actual_data_loss_hours:.1f}h exceeds "
                        f"target {impact.rpo_hours:.1f}h"
                    ),
                    event_time=current_time,
                )
            return True
        return False

    def get_impact(self, service_id: str) -> Optional[ServiceImpact]:
        return self._impacts.get(service_id)

    def get_all_impacts(self) -> list[ServiceImpact]:
        return list(self._impacts.values())

    def get_total_revenue_lost(self) -> float:
        return sum(i.revenue_lost for i in self._impacts.values())

    def get_total_sla_penalties(self) -> float:
        return sum(i.sla_penalties for i in self._impacts.values())

    def any_mtpd_breached(self) -> bool:
        return any(i.mtpd_breached for i in self._impacts.values())
