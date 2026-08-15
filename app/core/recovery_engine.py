"""
Recovery engine managing strategy execution with resource constraints
and PERT/triangular time sampling.

Per spec §12 and §15:
    - Recovery durations use optimistic/likely/pessimistic sampling
    - Resources are finite (team capacity, budget)
    - Each strategy has time, cost, data-loss, and risk characteristics
    - Decisions have consequences — not everything can run in parallel
"""

import random
from typing import Optional

from app.models.recovery import RecoveryStrategy, RecoveryPlan
from app.models.simulation import SimulationEvent, ResourcePool
from app.models.enums import EventType, ScoreCategory, StrategyType
from app.core.scoring import ScoringEngine


class RecoveryEngine:
    """
    Manages recovery strategy execution with:
    - PERT/triangular time sampling from seeded RNG
    - Resource constraint enforcement
    - Recovery event scheduling
    - Score impacts for recovery decisions
    """

    def __init__(
        self,
        run_id: str,
        rng: random.Random,
        scoring: ScoringEngine,
        resource_pool: ResourcePool,
    ):
        self.run_id = run_id
        self._rng = rng
        self._scoring = scoring
        self._resources = resource_pool
        self._active_plans: dict[str, RecoveryPlan] = {}  # system_id → plan
        self._completed_plans: list[RecoveryPlan] = []

    @property
    def resource_pool(self) -> ResourcePool:
        return self._resources

    def sample_recovery_duration(self, strategy: RecoveryStrategy) -> float:
        """
        Sample a recovery duration using triangular distribution.

        Uses the strategy's optimistic/likely/pessimistic time estimates
        and the seeded RNG for reproducibility.

        triangular(low=optimistic, high=pessimistic, mode=likely)
        """
        return self._rng.triangular(
            strategy.optimistic_hours,
            strategy.pessimistic_hours,
            strategy.likely_hours,
        )

    def can_start_recovery(self, strategy: RecoveryStrategy) -> bool:
        """Check if resources allow starting this recovery."""
        return self._resources.can_start_recovery(
            strategy.resource_cost, strategy.monetary_cost,
        )

    def get_available_strategies(
        self,
        strategies: list[RecoveryStrategy],
    ) -> list[RecoveryStrategy]:
        """Filter strategies to only those the current resources can support."""
        return [s for s in strategies if self.can_start_recovery(s)]

    def start_recovery(
        self,
        system_id: str,
        strategy: RecoveryStrategy,
        current_time: float,
        decision_id: str | None = None,
    ) -> tuple[Optional[RecoveryPlan], Optional[SimulationEvent]]:
        """
        Start a recovery action for a system.

        Returns:
            (recovery_plan, recovery_complete_event) or (None, None) if
            resources are insufficient.
        """
        if not self.can_start_recovery(strategy):
            self._scoring.record(
                category=ScoreCategory.RESOURCE_EFFICIENCY,
                delta=-5.0,
                reason=(
                    f"Recovery blocked for system {system_id}: "
                    f"insufficient resources "
                    f"(team: {self._resources.active_recoveries}/{self._resources.team_capacity}, "
                    f"budget: {self._resources.budget_remaining:.0f})"
                ),
                event_time=current_time,
                decision_id=decision_id,
            )
            return None, None

        # Sample duration from PERT distribution
        actual_duration = self.sample_recovery_duration(strategy)

        # Allocate resources
        self._resources.allocate(strategy.resource_cost, strategy.monetary_cost)

        # Create recovery plan
        plan = RecoveryPlan(
            run_id=self.run_id,
            system_id=system_id,
            strategy_id=strategy.id,
            decision_time=current_time,
            start_time=current_time,
            planned_duration=strategy.likely_hours,
            actual_duration=actual_duration,
            health_restored=1.0,
            resources_used=strategy.resource_cost,
            cost=strategy.monetary_cost,
        )
        self._active_plans[system_id] = plan

        # Score the decision
        self._scoring.record(
            category=ScoreCategory.RECOVERY_PERFORMANCE,
            delta=5.0,
            reason=(
                f"Recovery started for {system_id} using '{strategy.name}' "
                f"(estimated {actual_duration:.1f}h, cost {strategy.monetary_cost:.0f})"
            ),
            event_time=current_time,
            decision_id=decision_id,
        )

        if strategy.monetary_cost > 0:
            self._scoring.record(
                category=ScoreCategory.COST_EFFICIENCY,
                delta=-strategy.monetary_cost / 10000.0 * 5.0,
                reason=f"Recovery cost {strategy.monetary_cost:.0f} for {system_id}",
                event_time=current_time,
                decision_id=decision_id,
            )

        # Create completion event
        completion_event = SimulationEvent(
            run_id=self.run_id,
            event_type=EventType.RECOVERY_COMPLETE,
            time=current_time + actual_duration,
            priority=2,
            system_id=system_id,
            description=(
                f"Recovery of {system_id} via '{strategy.name}' completes "
                f"after {actual_duration:.1f}h"
            ),
            payload={
                "system_id": system_id,
                "strategy_id": strategy.id,
                "strategy_name": strategy.name,
                "actual_duration": actual_duration,
                "data_loss_hours": strategy.data_loss_hours,
                "cost": strategy.monetary_cost,
                "plan_id": plan.id,
            },
        )

        return plan, completion_event

    def complete_recovery(
        self,
        system_id: str,
        completion_time: float,
    ) -> Optional[RecoveryPlan]:
        """
        Mark a recovery as complete and release resources.

        Returns the completed plan or None if no active plan.
        """
        plan = self._active_plans.pop(system_id, None)
        if plan is None:
            return None

        plan.completion_time = completion_time
        plan.success = True
        self._resources.release()
        self._completed_plans.append(plan)

        self._scoring.record(
            category=ScoreCategory.RECOVERY_PERFORMANCE,
            delta=10.0,
            reason=(
                f"Recovery completed for {system_id} in {plan.actual_duration:.1f}h"
            ),
            event_time=completion_time,
        )

        return plan

    def get_active_plans(self) -> dict[str, RecoveryPlan]:
        return dict(self._active_plans)

    def get_completed_plans(self) -> list[RecoveryPlan]:
        return list(self._completed_plans)

    def is_system_recovering(self, system_id: str) -> bool:
        return system_id in self._active_plans

    def get_data_loss_hours(self, strategy: RecoveryStrategy) -> float:
        """Get data loss in hours for a strategy (RPO impact)."""
        return strategy.data_loss_hours
