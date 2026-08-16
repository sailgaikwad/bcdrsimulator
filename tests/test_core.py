"""
Tests for Phase 1.5 Core Engine components.

Validates:
- EventQueue priority ordering and FIFO tie-breaking
- ScoringEngine ledger and composite score calculation
- RiskEngine P*I*E calculation
- InvestigationEngine hidden fact narrowing
- BIAEngine impact accumulation and MTPD breaching
- FailurePropagationEngine partial capacity cascades
- RecoveryEngine resource constraints and sampling
- SimulationEngine headless execution and determinism
"""

import pytest
import random
from app.models.simulation import SimulationEvent, SimulationRun, ResourcePool
from app.models.enums import EventType, ScoreCategory, SimulationStatus, DependencyType, StrategyType, SystemType
from app.models.organization import BusinessService
from app.models.system import System, SystemState
from app.models.dependency import Dependency
from app.models.recovery import RecoveryStrategy
from app.graph.dependency_graph import DependencyGraph

from app.core.event_queue import EventQueue
from app.core.scoring import ScoringEngine
from app.core.risk_engine import RiskEngine
from app.core.investigation import InvestigationEngine
from app.core.bia_engine import BIAEngine
from app.core.failure_propagation import FailurePropagationEngine
from app.core.recovery_engine import RecoveryEngine
from app.core.simulation_engine import SimulationEngine


# ── EventQueue ───────────────────────────────────────────────────────

def test_event_queue_ordering():
    q = EventQueue()
    e1 = SimulationEvent(run_id="1", event_type=EventType.FAILURE, time=2.0, priority=1)
    e2 = SimulationEvent(run_id="1", event_type=EventType.FAILURE, time=1.0, priority=1)
    e3 = SimulationEvent(run_id="1", event_type=EventType.FAILURE, time=1.0, priority=0)
    e4 = SimulationEvent(run_id="1", event_type=EventType.FAILURE, time=1.0, priority=1) # tie with e2

    # push out of order
    q.push(e1)
    q.push(e2)
    q.push(e3)
    q.push(e4)

    # pop order should be:
    # 1. e3 (time 1.0, prio 0)
    # 2. e2 (time 1.0, prio 1, added first)
    # 3. e4 (time 1.0, prio 1, added second)
    # 4. e1 (time 2.0, prio 1)
    
    assert q.pop() == e3
    assert q.pop() == e2
    assert q.pop() == e4
    assert q.pop() == e1
    assert q.is_empty()


# ── ScoringEngine ────────────────────────────────────────────────────

def test_scoring_engine():
    scoring = ScoringEngine("run1")
    scoring.record(ScoreCategory.RECOVERY_PERFORMANCE, -10.0, "RTO breached", 1.0)
    scoring.record(ScoreCategory.COST_EFFICIENCY, 5.0, "Saved money", 2.0)
    
    ledger = scoring.get_ledger()
    assert len(ledger) == 2
    assert scoring.get_category_score(ScoreCategory.RECOVERY_PERFORMANCE) == 90.0
    assert scoring.get_category_score(ScoreCategory.COST_EFFICIENCY) == 105.0 # Max capped at 100 for composite
    
    # Base composite score calculation (normalized)
    # All are 100 except recovery(90), cost(100 due to cap).
    # weights: REC=0.25, DATA=0.20, BUS=0.25, RES=0.15, COST=0.15
    # score = 90*0.25 + 100*0.2 + 100*0.25 + 100*0.15 + 100*0.15 = 22.5 + 20 + 25 + 15 + 15 = 97.5
    assert scoring.get_composite_score() == 97.5


# ── RiskEngine ───────────────────────────────────────────────────────

def test_risk_engine():
    graph = DependencyGraph()
    graph.add_system(System(id="sys1", org_id="org1", name="App", system_type=SystemType.APPLICATION))
    graph.add_system(System(id="sys2", org_id="org1", name="DB", system_type=SystemType.DATABASE))
    graph.add_dependency(Dependency(id="d1", org_id="org1", source_id="sys1", target_id="sys2"))
    
    state = SystemState(system_id="sys1", health=0.0) # Down
    state.effective_availability = 0.0
    state.failed_at = 0.0
    
    risk = RiskEngine()
    assessment = risk.assess_system(
        run_id="run1",
        system_state=state,
        scenario_severity=1.0,
        bia_criticality=1.0,
        mtpd_hours=10.0,
        current_time=5.0, # 5 hours downtime
        dep_graph=graph
    )
    
    assert assessment.probability == 1.0 # 1.0 * (1 - 0.0)
    assert assessment.impact == 1.0
    
    # Exposure = min(1.0, 0.6*(5/10) + 0.4*(1 downstream / 2 total))
    # = 0.6*0.5 + 0.4*0.5 = 0.3 + 0.2 = 0.5
    assert assessment.exposure == 0.5
    assert assessment.risk_score == 0.5 # 1.0 * 1.0 * 0.5


# ── InvestigationEngine ──────────────────────────────────────────────

def test_investigation_engine():
    rng = random.Random(42)
    inv = InvestigationEngine("run1", rng)
    inv.register_fact("fact1", 0.7)
    
    # Initial view
    view = inv.get_user_view("fact1")
    assert view["range"] == [0.0, 1.0]
    assert view["confidence"] == 0.0
    
    # Investigate
    fact, cost = inv.investigate("fact1", "standard")
    assert cost == 1.0
    assert fact.confidence > 0.0
    assert fact.revealed_low > 0.0
    assert fact.revealed_high < 1.0
    assert fact.revealed_low <= 0.7 <= fact.revealed_high


# ── BIAEngine ────────────────────────────────────────────────────────

def test_bia_engine():
    scoring = ScoringEngine("run1")
    bia = BIAEngine("run1", scoring)
    
    svc = BusinessService(id="svc1", org_id="org1", name="Payments", mtpd_hours=10.0, revenue_per_hour=1000)
    bia.register_service(svc, ["sys1"])
    
    states = {"sys1": SystemState(system_id="sys1")}
    states["sys1"].effective_availability = 0.0 # Down
    
    bia.update_service_availability("svc1", states, 0.0, 0.0)
    impact = bia.get_impact("svc1")
    
    # Fast forward 11 hours
    triggered = bia.accumulate_impact(svc, impact, 11.0, 11.0)
    assert "mtpd_breached" in triggered
    assert impact.mtpd_breached is True
    assert impact.revenue_lost == 11000.0


# ── FailurePropagationEngine ─────────────────────────────────────────

def test_failure_propagation():
    graph = DependencyGraph()
    graph.add_system(System(id="sys1", org_id="org1", name="DB", system_type=SystemType.DATABASE))
    graph.add_system(System(id="sys2", org_id="org1", name="App1", system_type=SystemType.APPLICATION))
    graph.add_system(System(id="sys3", org_id="org1", name="App2", system_type=SystemType.APPLICATION))
    
    # App1 hard depends on DB
    graph.add_dependency(Dependency(id="d1", org_id="org1", source_id="sys1", target_id="sys2", dep_type=DependencyType.HARD))
    
    # App2 soft depends on DB
    graph.add_dependency(Dependency(id="d2", org_id="org1", source_id="sys1", target_id="sys3", dep_type=DependencyType.SOFT, weight=1.0))
    
    states = {
        "sys1": SystemState(system_id="sys1"),
        "sys2": SystemState(system_id="sys2"),
        "sys3": SystemState(system_id="sys3"),
    }
    
    # DB fails 50%
    states["sys1"].apply_damage(0.5, 0.0)
    
    prop = FailurePropagationEngine(graph)
    changes = prop.propagate_all(states)
    
    # sys1 effective = 0.5
    # sys2 (hard): own(1.0) * (0.5 * 1.0 + 0.0) = 0.5
    # sys3 (soft): own(1.0) * max(0, 1 - (0.5 * 1.0 * 0.3)) = 1.0 * 0.85 = 0.85
    assert states["sys2"].effective_availability == 0.5
    assert states["sys3"].effective_availability == 0.85


# ── RecoveryEngine ───────────────────────────────────────────────────

def test_recovery_engine():
    rng = random.Random(42)
    scoring = ScoringEngine("run1")
    pool = ResourcePool(team_capacity=2, budget_remaining=10000.0)
    rec = RecoveryEngine("run1", rng, scoring, pool)
    
    strat = RecoveryStrategy(id="st1", name="Restore", strategy_type=StrategyType.BACKUP_RESTORE,
                            optimistic_hours=1.0, likely_hours=2.0, pessimistic_hours=4.0,
                            resource_cost=1.0, monetary_cost=5000.0)
                            
    # Start
    plan, event = rec.start_recovery("sys1", strat, 0.0)
    assert plan is not None
    assert event is not None
    assert pool.active_recoveries == 1
    assert pool.budget_remaining == 5000.0
    
    # Second should pass
    plan2, _ = rec.start_recovery("sys2", strat, 0.0)
    assert plan2 is not None
    assert pool.active_recoveries == 2
    
    # Third should fail (no capacity/budget)
    plan3, _ = rec.start_recovery("sys3", strat, 0.0)
    assert plan3 is None


# ── SimulationEngine ─────────────────────────────────────────────────

def test_simulation_engine_determinism():
    """Verify that using the same seed produces the same exact score and time."""
    def run_sim(seed):
        run_data = SimulationRun(id=f"run-{seed}", org_id="org1", scenario_id="scen1", rng_seed=seed)
        graph = DependencyGraph()
        graph.add_system(System(id="sys1", org_id="org1", name="DB", system_type=SystemType.DATABASE))
        
        svc = BusinessService(id="svc1", org_id="org1", name="Service", mtpd_hours=100.0)
        
        engine = SimulationEngine(
            run_data=run_data,
            dep_graph=graph,
            services=[svc],
            service_systems_map={"svc1": ["sys1"]},
            resource_pool=ResourcePool(team_capacity=5)
        )
        
        engine.trigger_disaster({"sys1": 1.0})
        
        # Add a recovery event
        strat = RecoveryStrategy(id="st1", name="Restore", strategy_type=StrategyType.BACKUP_RESTORE,
                            optimistic_hours=2.0, likely_hours=4.0, pessimistic_hours=10.0)
        
        # This samples from the RNG
        plan, evt = engine.recovery.start_recovery("sys1", strat, 0.0)
        engine.schedule_event(evt)
        
        engine.run_until_empty()
        return plan.actual_duration, engine.scoring.get_composite_score()
        
    dur1, score1 = run_sim(42)
    dur2, score2 = run_sim(42)
    dur3, score3 = run_sim(99)
    
    assert dur1 == dur2
    assert score1 == score2
    assert dur1 != dur3 # Different seed should yield different duration

def test_finserve_dependency_propagation():
    """Verify FinServe dependency graph processes Event 1 & Event 2 correctly."""
    run_data = SimulationRun(id="run1", org_id="org1", scenario_id="scen1", rng_seed=42)
    graph = DependencyGraph()
    
    # Systems
    sys_igw = System(id="sys-igw", org_id="org1", name="Internet Gateway", system_type=SystemType.GATEWAY)
    sys_fw = System(id="sys-fw", org_id="org1", name="Firewall", system_type=SystemType.FIREWALL)
    sys_app = System(id="sys-app", org_id="org1", name="Application Cluster", system_type=SystemType.APPLICATION)
    sys_db_primary = System(id="sys-db-pri", org_id="org1", name="Primary Database", system_type=SystemType.DATABASE)
    sys_cache = System(id="sys-cache", org_id="org1", name="Cache", system_type=SystemType.CACHE)
    
    for s in [sys_igw, sys_fw, sys_app, sys_db_primary, sys_cache]:
        graph.add_system(s)
        
    # The corrected dependencies
    graph.add_dependency(Dependency(id="d1", org_id="org1", source_id="sys-igw", target_id="sys-fw", dep_type=DependencyType.HARD))
    graph.add_dependency(Dependency(id="d2", org_id="org1", source_id="sys-fw", target_id="sys-app", dep_type=DependencyType.HARD))
    graph.add_dependency(Dependency(id="d3", org_id="org1", source_id="sys-db-pri", target_id="sys-app", dep_type=DependencyType.HARD))
    graph.add_dependency(Dependency(id="d4", org_id="org1", source_id="sys-cache", target_id="sys-app", dep_type=DependencyType.SOFT, weight=0.3))
    
    engine = SimulationEngine(
        run_data=run_data,
        dep_graph=graph,
        services=[],
        service_systems_map={},
        resource_pool=ResourcePool()
    )
    
    # Trigger Disaster (Event 1): Primary DB fails 100%
    engine.trigger_disaster({"sys-db-pri": 1.0})
    
    # compute_initial_cascade propagates immediately
    assert engine.system_states["sys-db-pri"].health == 0.0
    
    # Now Application Cluster should have effective availability 0.0 due to HARD dependency on DB
    assert engine.system_states["sys-app"].effective_availability == 0.0
