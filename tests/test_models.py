"""
Tests for Pydantic domain models.

Validates:
- Model creation with defaults
- Field validation (bounds, enums)
- SystemState damage/recovery mechanics
- HiddenFact reveal_range narrowing
- RiskAssessment P×I×E computation
- ResourcePool allocation logic
- RiskLevel.from_score thresholds
"""

import pytest
from app.models.enums import (
    SystemType, SystemTier, SystemStatus, DependencyType,
    StrategyType, RiskLevel, ScoreCategory, EventType,
    SimulationStatus, DisasterCategory,
)
from app.models.organization import Organization, BusinessService
from app.models.system import System, SystemState
from app.models.dependency import Dependency
from app.models.disaster import DisasterScenario, AffectedSystem
from app.models.recovery import RecoveryStrategy, RecoveryPlan
from app.models.simulation import (
    SimulationRun, SimulationEvent, ScoreEvent,
    HiddenFact, RiskAssessment, ResourcePool,
)


# ── Organization & BusinessService ──────────────────────────────────

class TestOrganization:
    def test_create_with_defaults(self):
        org = Organization(name="Test Corp")
        assert org.name == "Test Corp"
        assert org.id  # UUID generated
        assert org.industry is None

    def test_create_with_all_fields(self):
        org = Organization(id="org-1", name="FinServe", industry="Finance")
        assert org.id == "org-1"
        assert org.industry == "Finance"


class TestBusinessService:
    def test_create_with_defaults(self):
        svc = BusinessService(org_id="org-1", name="Payments")
        assert svc.criticality == 5
        assert svc.rto_hours == 4.0
        assert svc.rpo_hours == 1.0
        assert svc.mtpd_hours == 24.0

    def test_criticality_bounds(self):
        with pytest.raises(Exception):
            BusinessService(org_id="org-1", name="X", criticality=0)
        with pytest.raises(Exception):
            BusinessService(org_id="org-1", name="X", criticality=11)

    def test_valid_criticality_range(self):
        for c in range(1, 11):
            svc = BusinessService(org_id="org-1", name="X", criticality=c)
            assert svc.criticality == c


# ── System & SystemState ────────────────────────────────────────────

class TestSystem:
    def test_create(self):
        sys = System(org_id="org-1", name="DB Primary", system_type=SystemType.DATABASE)
        assert sys.system_type == SystemType.DATABASE
        assert sys.tier == SystemTier.STANDARD
        assert sys.base_health == 1.0

    def test_health_bounds(self):
        with pytest.raises(Exception):
            System(org_id="org-1", name="X", system_type=SystemType.SERVER, base_health=1.5)


class TestSystemState:
    def test_initial_state(self):
        state = SystemState(system_id="sys-1")
        assert state.health == 1.0
        assert state.status == SystemStatus.OPERATIONAL
        assert state.is_operational
        assert not state.is_down

    def test_apply_damage_partial(self):
        state = SystemState(system_id="sys-1")
        state.apply_damage(0.4, time=1.0)
        assert state.health == pytest.approx(0.6)
        assert state.status == SystemStatus.DEGRADED

    def test_apply_damage_total(self):
        state = SystemState(system_id="sys-1")
        state.apply_damage(1.0, time=1.0)
        assert state.health == 0.0
        assert state.status == SystemStatus.FAILED
        assert state.is_down
        assert state.failed_at == 1.0

    def test_apply_damage_clamps(self):
        state = SystemState(system_id="sys-1")
        state.apply_damage(2.0, time=1.0)
        assert state.health == 0.0

    def test_apply_recovery(self):
        state = SystemState(system_id="sys-1", health=0.0, status=SystemStatus.FAILED)
        state.apply_recovery(0.5, time=2.0)
        assert state.health == 0.5
        assert state.status == SystemStatus.RECOVERING

    def test_apply_recovery_full(self):
        state = SystemState(system_id="sys-1", health=0.3, status=SystemStatus.RECOVERING)
        state.apply_recovery(0.7, time=3.0)
        assert state.health == 1.0
        assert state.status == SystemStatus.RESTORED
        assert state.restored_at == 3.0

    def test_apply_recovery_clamps(self):
        state = SystemState(system_id="sys-1", health=0.8, status=SystemStatus.DEGRADED)
        state.apply_recovery(0.5, time=3.0)
        assert state.health == 1.0

    def test_failed_at_recorded_once(self):
        state = SystemState(system_id="sys-1")
        state.apply_damage(1.0, time=1.0)
        assert state.failed_at == 1.0
        # Further damage shouldn't change failed_at
        state.health = 0.5
        state.apply_damage(0.5, time=2.0)
        assert state.failed_at == 1.0  # still the original time


# ── Dependency ──────────────────────────────────────────────────────

class TestDependency:
    def test_create_hard(self):
        dep = Dependency(
            org_id="org-1", source_id="s1", target_id="s2",
            dep_type=DependencyType.HARD, weight=1.0,
        )
        assert dep.dep_type == DependencyType.HARD
        assert dep.weight == 1.0

    def test_weight_bounds(self):
        with pytest.raises(Exception):
            Dependency(org_id="org-1", source_id="s1", target_id="s2", weight=1.5)
        with pytest.raises(Exception):
            Dependency(org_id="org-1", source_id="s1", target_id="s2", weight=-0.1)


# ── DisasterScenario ────────────────────────────────────────────────

class TestDisasterScenario:
    def test_create(self):
        scenario = DisasterScenario(
            name="DB Failure",
            category=DisasterCategory.DATABASE_FAILURE,
            severity=0.8,
            affected_systems=[
                AffectedSystem(system_id="db-1", health_impact=1.0),
            ],
            hidden_facts={"backup_integrity": 0.6},
        )
        assert scenario.severity == 0.8
        assert len(scenario.affected_systems) == 1
        assert scenario.hidden_facts["backup_integrity"] == 0.6


# ── RecoveryStrategy ────────────────────────────────────────────────

class TestRecoveryStrategy:
    def test_create(self):
        strat = RecoveryStrategy(
            name="Hot Standby",
            strategy_type=StrategyType.HOT_STANDBY,
            optimistic_hours=0.25,
            likely_hours=0.5,
            pessimistic_hours=1.0,
        )
        assert strat.strategy_type == StrategyType.HOT_STANDBY
        assert strat.likely_hours == 0.5


# ── SimulationEvent ordering ────────────────────────────────────────

class TestSimulationEvent:
    def test_ordering_by_time(self):
        e1 = SimulationEvent(run_id="r1", event_type=EventType.FAILURE, time=1.0)
        e2 = SimulationEvent(run_id="r1", event_type=EventType.RECOVERY_START, time=2.0)
        assert e1 < e2

    def test_ordering_by_priority(self):
        e1 = SimulationEvent(run_id="r1", event_type=EventType.FAILURE, time=1.0, priority=1)
        e2 = SimulationEvent(run_id="r1", event_type=EventType.DEGRADATION, time=1.0, priority=5)
        assert e1 < e2


# ── HiddenFact ──────────────────────────────────────────────────────

class TestHiddenFact:
    def test_initial_state(self):
        fact = HiddenFact(
            run_id="r1", fact_key="backup_integrity",
            true_value=0.6, revealed_low=0.0, revealed_high=1.0,
        )
        assert fact.confidence == 0.0
        assert not fact.investigated

    def test_reveal_narrows_range(self):
        fact = HiddenFact(
            run_id="r1", fact_key="backup_integrity",
            true_value=0.6, revealed_low=0.0, revealed_high=1.0,
        )
        low, high = fact.reveal_range(accuracy=0.5)
        assert low > 0.0
        assert high < 1.0
        assert low <= fact.true_value <= high
        assert fact.confidence > 0.0
        assert fact.investigated

    def test_reveal_always_contains_truth(self):
        """The revealed range must always contain the true value."""
        fact = HiddenFact(
            run_id="r1", fact_key="test",
            true_value=0.3, revealed_low=0.0, revealed_high=1.0,
        )
        for acc in [0.1, 0.3, 0.5, 0.8, 1.0]:
            low, high = fact.reveal_range(accuracy=acc)
            assert low <= fact.true_value <= high, (
                f"Range [{low}, {high}] does not contain true value {fact.true_value}"
            )


# ── RiskAssessment ──────────────────────────────────────────────────

class TestRiskAssessment:
    def test_compute(self):
        ra = RiskAssessment(
            run_id="r1", probability=0.8, impact=0.9, exposure=0.7,
        )
        score = ra.compute()
        assert score == pytest.approx(0.8 * 0.9 * 0.7)
        assert ra.risk_level == RiskLevel.HIGH  # 0.504 → HIGH (0.5–0.8 range)

    def test_risk_levels(self):
        assert RiskLevel.from_score(0.1) == RiskLevel.LOW
        assert RiskLevel.from_score(0.3) == RiskLevel.MEDIUM
        assert RiskLevel.from_score(0.6) == RiskLevel.HIGH
        assert RiskLevel.from_score(0.9) == RiskLevel.CRITICAL
        assert RiskLevel.from_score(0.0) == RiskLevel.LOW
        assert RiskLevel.from_score(1.0) == RiskLevel.CRITICAL


# ── ResourcePool ────────────────────────────────────────────────────

class TestResourcePool:
    def test_can_start(self):
        pool = ResourcePool(team_capacity=2, budget_remaining=10000)
        assert pool.can_start_recovery(1.0, 5000)

    def test_cannot_start_over_capacity(self):
        pool = ResourcePool(team_capacity=1, active_recoveries=1)
        assert not pool.can_start_recovery(1.0, 0)

    def test_cannot_start_over_budget(self):
        pool = ResourcePool(team_capacity=3, budget_remaining=100)
        assert not pool.can_start_recovery(1.0, 200)

    def test_allocate_and_release(self):
        pool = ResourcePool(team_capacity=2, budget_remaining=10000)
        pool.allocate(1.0, 3000)
        assert pool.active_recoveries == 1
        assert pool.budget_remaining == 7000
        pool.release()
        assert pool.active_recoveries == 0
