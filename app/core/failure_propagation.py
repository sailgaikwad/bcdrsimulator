"""
Failure propagation engine using weighted partial-capacity model.

Propagates failures through the dependency graph using:
- Hard dependencies: proportional reduction (multiplicative)
- Soft dependencies: additive penalty with floor (degrades, doesn't kill)
- Dependency weights: coupling strength (0.0–1.0)

Per spec §9:
    effective_availability = own_health × dependency_factor

The propagation follows topological order to ensure upstream
systems are processed before their dependents.
"""

from app.models.system import SystemState
from app.models.dependency import Dependency
from app.models.enums import DependencyType, SystemStatus, EventType
from app.models.simulation import SimulationEvent
from app.graph.dependency_graph import DependencyGraph


# Soft dependency penalty factor — controls how much soft deps degrade
_SOFT_PENALTY_FACTOR = 0.3

# Threshold below which a system is considered failed enough to propagate
_PROPAGATION_THRESHOLD = 0.5


class FailurePropagationEngine:
    """
    Propagates failures through the dependency graph with weighted
    partial-capacity semantics.

    Algorithm:
        1. Start with initially damaged systems
        2. Process systems in topological order (upstream first)
        3. For each system, compute effective_availability based on:
           - own_health (direct damage)
           - upstream hard dependencies (multiplicative reduction)
           - upstream soft dependencies (additive penalty, capped)
        4. If effective_availability drops below threshold, schedule
           cascade events for downstream systems

    This creates realistic partial-degradation cascades rather than
    binary UP/DOWN behavior.
    """

    def __init__(self, dep_graph: DependencyGraph):
        self._graph = dep_graph

    def compute_effective_availability(
        self,
        system_id: str,
        system_states: dict[str, SystemState],
    ) -> float:
        """
        Compute effective availability for a system accounting for
        its own health AND upstream dependency health.

        Formula:
            effective = own_health × hard_factor × soft_factor

            hard_factor = ∏ (upstream_eff × weight + (1 - weight))
                          for each hard dependency

            soft_factor = max(0, 1 - Σ((1 - upstream_eff) × weight × 0.3))
                          for each soft dependency
        """
        state = system_states.get(system_id)
        if state is None:
            return 1.0

        own_health = state.health
        hard_factor = 1.0
        soft_penalty = 0.0

        for upstream_id, edge_data in self._graph.get_upstream(system_id):
            upstream_state = system_states.get(upstream_id)
            if upstream_state is None:
                continue

            upstream_eff = upstream_state.effective_availability
            weight = edge_data.get("weight", 1.0)
            dep_type = edge_data.get("dep_type", "hard")

            if dep_type == DependencyType.DATA_SYNC.value or dep_type == DependencyType.DATA_SYNC:
                # Sync dependency: degraded source leads to stale/unsynced replica
                hard_factor *= (upstream_eff * weight + (1.0 - weight))
            elif dep_type == DependencyType.HARD.value or dep_type == DependencyType.HARD:
                # Hard dependency: multiplicative reduction
                hard_factor *= (upstream_eff * weight + (1.0 - weight))
            else:
                # Soft dependency: additive penalty
                soft_penalty += (1.0 - upstream_eff) * weight * _SOFT_PENALTY_FACTOR

        soft_factor = max(0.0, 1.0 - soft_penalty)
        effective = own_health * hard_factor * soft_factor

        return max(0.0, min(1.0, effective))

    def propagate_all(
        self,
        system_states: dict[str, SystemState],
    ) -> dict[str, float]:
        """
        Recompute effective_availability for ALL systems in topological order.

        Returns a dict of system_id → new effective_availability.
        Also updates the SystemState objects in place.
        """
        order = self._graph.get_topological_order()
        changes = {}

        for system_id in order:
            state = system_states.get(system_id)
            if state is None:
                continue

            old_eff = state.effective_availability
            new_eff = self.compute_effective_availability(system_id, system_states)
            state.effective_availability = new_eff

            if abs(old_eff - new_eff) > 0.001:
                changes[system_id] = new_eff

                # Update status based on effective availability
                if new_eff == 0.0:
                    if state.status != SystemStatus.FAILED:
                        state.status = SystemStatus.FAILED
                elif new_eff < 1.0:
                    if state.status == SystemStatus.OPERATIONAL:
                        state.status = SystemStatus.DEGRADED

        return changes

    def get_initial_failure_events(
        self,
        initially_damaged: dict[str, float],
        run_id: str,
        base_time: float,
    ) -> list[SimulationEvent]:
        """Generate the initial FAILURE events without mutating state."""
        events = []
        for system_id, damage in initially_damaged.items():
            node_data = self._graph.get_node_data(system_id)
            name = node_data.get("name", system_id) if node_data else system_id
            events.append(SimulationEvent(
                run_id=run_id,
                event_type=EventType.FAILURE,
                time=base_time,
                priority=1,
                system_id=system_id,
                description=f"Initial failure triggered for {name}",
                payload={
                    "damage": damage,
                    "cause": "disaster_trigger",
                },
            ))
        return events

    def get_downstream_propagation_events(
        self,
        system_id: str,
        run_id: str,
        base_time: float,
    ) -> list[SimulationEvent]:
        """Generate PROPAGATION events for immediate downstream neighbors."""
        events = []
        for target_id, _ in self._graph.get_downstream(system_id):
            node_data = self._graph.get_node_data(target_id)
            name = node_data.get("name", target_id) if node_data else target_id
            events.append(SimulationEvent(
                run_id=run_id,
                event_type=EventType.PROPAGATION,
                time=base_time,  # Use same time; queue priority handles ordering
                priority=3,
                system_id=target_id,
                description=f"Evaluating propagation impact for {name}",
                payload={
                    "cause": "upstream_change",
                    "upstream_id": system_id
                },
            ))
        return events
