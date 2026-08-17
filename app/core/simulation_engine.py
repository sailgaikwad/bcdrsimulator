"""
Headless Discrete-Event Simulation Engine.

Ties together all Phase 1.5 components:
- EventQueue
- FailurePropagationEngine
- RecoveryEngine
- RiskEngine
- ScoringEngine
- InvestigationEngine
- BIAEngine

This is the main entry point for running a simulation. It is completely
decoupled from Streamlit, allowing for CLI, Monte Carlo, and automated tests.

Per spec §11, §13, and §16.
"""

import random
from typing import Optional, Any

from app.models.simulation import SimulationRun, SimulationEvent, ResourcePool
from app.models.enums import EventType, SimulationStatus, SystemStatus, ScoreCategory
from app.models.system import SystemState
from app.models.organization import BusinessService
from app.graph.dependency_graph import DependencyGraph

from app.core.event_queue import EventQueue
from app.core.failure_propagation import FailurePropagationEngine
from app.core.recovery_engine import RecoveryEngine
from app.core.risk_engine import RiskEngine
from app.core.scoring import ScoringEngine
from app.core.investigation import InvestigationEngine
from app.core.bia_engine import BIAEngine


class SimulationEngine:
    """
    Main controller for a single simulation run.

    Uses a discrete-event loop to process events in time order.
    The simulation is fully deterministic for a given seed.
    """

    def __init__(
        self,
        run_data: SimulationRun,
        dep_graph: DependencyGraph,
        services: list[BusinessService],
        service_systems_map: dict[str, list[str]],
        resource_pool: ResourcePool,
    ):
        self.run_data = run_data
        self.dep_graph = dep_graph
        self.services = services

        # Initialize RNG with the seeded value
        self.rng = random.Random(run_data.rng_seed)

        # Core engines
        self.events = EventQueue()
        self.processed_events = []
        self.scoring = ScoringEngine(run_data.id)
        self.investigation = InvestigationEngine(run_data.id, self.rng)
        self.propagation = FailurePropagationEngine(dep_graph)
        self.risk = RiskEngine()
        self.bia = BIAEngine(run_data.id, self.scoring)

        # Runtime state
        self.current_time: float = 0.0
        self.system_states: dict[str, SystemState] = {}

        self.recovery = RecoveryEngine(run_data.id, self.rng, self.scoring, resource_pool, self.dep_graph, self.system_states)

        # Initialize runtime state for all systems
        for sys_id in self.dep_graph.get_all_system_ids():
            sys_data = self.dep_graph.get_node_data(sys_id)
            if sys_data:
                self.system_states[sys_id] = SystemState(
                    system_id=sys_id,
                    health=sys_data.get("base_health", 1.0)
                )

        # Register services with BIA engine
        for svc in services:
            self.bia.register_service(svc, service_systems_map.get(svc.id, []))

    def schedule_event(self, event: SimulationEvent) -> None:
        """Add an event to the priority queue."""
        self.events.push(event)

    def trigger_disaster(
        self,
        initial_damage: dict[str, float],
        scenario_severity: float = 1.0,
    ) -> None:
        """
        Trigger the initial disaster.

        Args:
            initial_damage: {system_id: damage_amount}
            scenario_severity: 0.0 to 1.0
        """
        self.run_data.status = SimulationStatus.RUNNING

        events = self.propagation.get_initial_failure_events(
            initial_damage,
            self.run_data.id,
            self.current_time,
        )

        for event in events:
            # Process the initial disaster impact immediately
            self._handle_failure(event)
            self.processed_events.append(event)

        # Update BIA after initial impact
        self._update_bia(dt=0.0)

    def step(self) -> Optional[SimulationEvent]:
        """
        Process the next event in the queue.

        Returns the processed event, or None if the queue is empty.
        """
        event = self.events.pop()
        if not event:
            return None

        # Advance clock and accumulate BIA impact for the elapsed time
        dt = event.time - self.current_time
        if dt > 0:
            self.current_time = event.time
            self._update_bia(dt)

        # Route event to appropriate handler
        if event.event_type == EventType.FAILURE:
            self._handle_failure(event)
        elif event.event_type == EventType.PROPAGATION:
            self._handle_propagation(event)
        elif event.event_type == EventType.RECOVERY_START:
            self._handle_recovery_start(event)
        elif event.event_type == EventType.RECOVERY_COMPLETE:
            self._handle_recovery_complete(event)
        elif event.event_type == EventType.INVESTIGATION_COMPLETE:
            self._handle_investigation_complete(event)
        elif event.event_type == EventType.USER_DECISION:
            self._handle_user_decision(event)

        self.processed_events.append(event)
        return event

    def run_until_empty(self) -> None:
        """Run the simulation until the event queue is empty or business fails."""
        while not self.events.is_empty():
            if self.run_data.status in (SimulationStatus.COMPLETED, SimulationStatus.FAILED):
                break
            self.step()

        if self.run_data.status == SimulationStatus.RUNNING:
            self.run_data.status = SimulationStatus.COMPLETED
            self.run_data.end_time = self.current_time

    def _update_bia(self, dt: float) -> None:
        """Update BIA engine and check for critical failures."""
        for svc in self.services:
            self.bia.update_service_availability(
                svc.id, self.system_states, self.current_time, dt
            )
            impact = self.bia.get_impact(svc.id)
            if impact:
                triggered = self.bia.accumulate_impact(
                    svc, impact, self.current_time, dt
                )

                # If any service breaches MTPD, the whole run fails
                if "mtpd_breached" in triggered:
                    self.run_data.status = SimulationStatus.FAILED
                    self.run_data.end_time = self.current_time
                    self.events.clear()

    def _handle_failure(self, event: SimulationEvent) -> None:
        """Handle a direct failure event."""
        sys_id = event.system_id
        if not sys_id:
            return

        damage = event.payload.get("damage", 1.0)
        state = self.system_states.get(sys_id)
        if state:
            state.apply_damage(damage, self.current_time)
            state.effective_availability = self.propagation.compute_effective_availability(sys_id, self.system_states)

            target_name = sys_id
            target_data = self.dep_graph.get_node_data(sys_id)
            if target_data and "name" in target_data:
                target_name = target_data["name"]

            self.scoring.record(
                category=ScoreCategory.BUSINESS_AVAILABILITY,
                delta=-10.0 * damage,
                reason=f"{target_name} suffered {damage:.0%} direct failure damage.",
                event_time=self.current_time
            )

            # Schedule downstream effects
            prop_events = self.propagation.get_downstream_propagation_events(
                sys_id, self.run_data.id, self.current_time
            )
            for e in prop_events:
                self.schedule_event(e)

    def _handle_propagation(self, event: SimulationEvent) -> None:
        """Handle a propagation event."""
        sys_id = event.system_id
        if not sys_id:
            return

        state = self.system_states.get(sys_id)
        if not state:
            return

        old_eff = state.effective_availability
        new_eff = self.propagation.compute_effective_availability(sys_id, self.system_states)

        if abs(old_eff - new_eff) > 0.001:
            state.effective_availability = new_eff

            # Update status and timestamps
            if new_eff == 0.0:
                if state.status != SystemStatus.FAILED:
                    state.status = SystemStatus.FAILED
                if state.failed_at is None:
                    state.failed_at = self.current_time
            elif new_eff < 1.0:
                if state.status == SystemStatus.OPERATIONAL:
                    state.status = SystemStatus.DEGRADED
                if state.failed_at is None:
                    state.failed_at = self.current_time
            elif new_eff == 1.0:
                if state.status != SystemStatus.OPERATIONAL:
                    state.status = SystemStatus.OPERATIONAL
                if old_eff < 1.0:
                    state.restored_at = self.current_time

            # Since this node changed, propagate further downstream
            prop_events = self.propagation.get_downstream_propagation_events(
                sys_id, self.run_data.id, self.current_time
            )
            for e in prop_events:
                self.schedule_event(e)

            # Log the change
            target_name = sys_id
            target_data = self.dep_graph.get_node_data(sys_id)
            if target_data and "name" in target_data:
                target_name = target_data["name"]

            upstream_id = event.payload.get("upstream_id")
            upstream_name = upstream_id
            if upstream_id:
                up_data = self.dep_graph.get_node_data(upstream_id)
                if up_data and "name" in up_data:
                    upstream_name = up_data["name"]

            if new_eff == 0.0:
                event.description = f"{target_name} failed completely (0%) due to upstream {upstream_name} state change."
                self.scoring.record(ScoreCategory.BUSINESS_AVAILABILITY, -5.0, event.description, self.current_time)
            elif new_eff < 1.0 and new_eff < old_eff:
                event.description = f"{target_name} health degraded to {new_eff:.0%} due to upstream {upstream_name} degradation."
                self.scoring.record(ScoreCategory.BUSINESS_AVAILABILITY, -2.0, event.description, self.current_time)
            elif new_eff < 1.0 and new_eff > old_eff:
                event.description = f"{target_name} health improved to {new_eff:.0%} following upstream {upstream_name} recovery."
                self.scoring.record(ScoreCategory.BUSINESS_AVAILABILITY, 2.0, event.description, self.current_time)
            elif new_eff == 1.0:
                event.description = f"{target_name} fully recovered to 100% following upstream {upstream_name} recovery."
                self.scoring.record(ScoreCategory.BUSINESS_AVAILABILITY, 5.0, event.description, self.current_time)
        else:
            event.description = f"Propagation check for {sys_id}: no change in availability."

    def _handle_recovery_start(self, event: SimulationEvent) -> None:
        """Handle the start of a recovery action."""
        # Managed via the API usually, but if scheduled, we might trigger it here
        pass

    def _handle_recovery_complete(self, event: SimulationEvent) -> None:
        """Handle the completion of a recovery action."""
        sys_id = event.system_id
        if not sys_id:
            return

        plan = self.recovery.complete_recovery(sys_id, self.current_time)
        if plan:
            state = self.system_states.get(sys_id)
            if state:
                state.apply_recovery(plan.health_restored, self.current_time)
                state.effective_availability = self.propagation.compute_effective_availability(sys_id, self.system_states)

                # Recompute propagation downstream
                prop_events = self.propagation.get_downstream_propagation_events(
                    sys_id, self.run_data.id, self.current_time
                )
                for e in prop_events:
                    self.schedule_event(e)

                # Tell BIA about technical recovery (simplification: if eff_avail >= 1.0)
                if state.effective_availability >= 1.0:
                    for svc_id, sys_list in self.bia._service_system_map.items():
                        if sys_id in sys_list:
                            self.bia.record_technical_recovery(svc_id, self.current_time)

                            # Add a WRT (Work Recovery Time) delay before business recovery
                            # We'll schedule a business recovery event 2 hours later
                            wrt_delay = 2.0
                            self.schedule_event(SimulationEvent(
                                run_id=self.run_data.id,
                                event_type=EventType.RECOVERY_COMPLETE,
                                time=self.current_time + wrt_delay,
                                priority=4,
                                system_id=sys_id, # using system_id to route, but it's for business
                                description=f"Business operations restored for {svc_id} (WRT complete)",
                                payload={"business_recovery_for": svc_id}
                            ))

        # Handle business recovery
        svc_id = event.payload.get("business_recovery_for")
        if svc_id:
            self.bia.record_business_recovery(svc_id, self.current_time)

    def _handle_investigation_complete(self, event: SimulationEvent) -> None:
        """Handle completion of an investigation."""
        fact_key = event.payload.get("fact_key")
        inv_type = event.payload.get("investigation_type", "standard")
        if fact_key:
            fact, cost = self.investigation.investigate(fact_key, inv_type)

    def _handle_user_decision(self, event: SimulationEvent) -> None:
        """Handle a user decision."""
        pass
