import streamlit as st
import os

from app.database.sqlite_manager import SQLiteManager
from app.database.repositories import (
    OrganizationRepository, BusinessServiceRepository, SystemRepository,
    DependencyRepository, RecoveryStrategyRepository, DisasterScenarioRepository
)
from app.models.organization import Organization, BusinessService
from app.models.system import System
from app.models.dependency import Dependency
from app.models.recovery import RecoveryStrategy
from app.models.simulation import SimulationRun, ResourcePool, ScoreEvent
from app.models.enums import SystemType, DependencyType, StrategyType, DisasterCategory
from app.models.disaster import DisasterScenario, AffectedSystem
from app.graph.dependency_graph import DependencyGraph
from app.core.simulation_engine import SimulationEngine
from app.cloud.gcp_exporter import GCPExporter
import json
from app.database.repositories import SimulationRunRepository


def init_session_state():
    """Ensure all required objects exist in session_state."""
    if "db" not in st.session_state:
        # Use a local persistent DB for UI
        db = SQLiteManager("bcdr.db")
        db.initialize()
        st.session_state["db"] = db
        
        # Load demo data if empty
        org_repo = OrganizationRepository(db)
        if len(org_repo.list_all()) == 0:
            _load_finserve_demo(db)
            
    if "engine" not in st.session_state:
        _init_simulation_engine()


def reset_simulation():
    """Clear the active simulation and recreate the engine."""
    if "engine" in st.session_state:
        del st.session_state["engine"]
    _init_simulation_engine()


def _load_finserve_demo(db: SQLiteManager):
    """Seed the database with FinServe Demo Data."""
    org_repo = OrganizationRepository(db)
    svc_repo = BusinessServiceRepository(db)
    sys_repo = SystemRepository(db)
    dep_repo = DependencyRepository(db)
    strat_repo = RecoveryStrategyRepository(db)
    scenario_repo = DisasterScenarioRepository(db)
    
    org = Organization(id="org-finserve", name="FinServe Demo", industry="Finance")
    org_repo.save(org)

    # Services
    svc_payment = BusinessService(
        id="svc-payment", org_id=org.id, name="Payment Processing",
        criticality=10, rto_hours=1.0, rpo_hours=0.5, mtpd_hours=4.0, revenue_per_hour=50000.0
    )
    svc_portal = BusinessService(
        id="svc-portal", org_id=org.id, name="Customer Portal",
        criticality=8, rto_hours=4.0, rpo_hours=1.0, mtpd_hours=12.0, revenue_per_hour=10000.0
    )
    svc_report = BusinessService(
        id="svc-report", org_id=org.id, name="Internal Reporting",
        criticality=4, rto_hours=24.0, rpo_hours=24.0, mtpd_hours=72.0, revenue_per_hour=500.0
    )
    for svc in [svc_payment, svc_portal, svc_report]:
        svc_repo.save(svc)

    # Systems
    sys_igw = System(id="sys-igw", org_id=org.id, name="Internet Gateway", system_type=SystemType.GATEWAY)
    sys_fw = System(id="sys-fw", org_id=org.id, name="Firewall", system_type=SystemType.FIREWALL)
    sys_app = System(id="sys-app", org_id=org.id, name="Application Cluster", system_type=SystemType.APPLICATION)
    sys_db_primary = System(id="sys-db-pri", org_id=org.id, name="Primary Database", system_type=SystemType.DATABASE)
    sys_db_replica = System(id="sys-db-rep", org_id=org.id, name="Read Replica", system_type=SystemType.DATABASE)
    sys_cache = System(id="sys-cache", org_id=org.id, name="Cache", system_type=SystemType.CACHE)
    sys_backup = System(id="sys-backup", org_id=org.id, name="Backup System", system_type=SystemType.BACKUP)
    
    systems = [sys_igw, sys_fw, sys_app, sys_db_primary, sys_db_replica, sys_cache, sys_backup]
    for sys in systems:
        sys_repo.save(sys)

    deps = [
        Dependency(id="d1", org_id=org.id, source_id=sys_igw.id, target_id=sys_fw.id, dep_type=DependencyType.HARD),
        Dependency(id="d2", org_id=org.id, source_id=sys_fw.id, target_id=sys_app.id, dep_type=DependencyType.HARD),
        Dependency(id="d3", org_id=org.id, source_id=sys_db_primary.id, target_id=sys_app.id, dep_type=DependencyType.HARD),
        Dependency(id="d4", org_id=org.id, source_id=sys_cache.id, target_id=sys_app.id, dep_type=DependencyType.SOFT, weight=0.3),
        Dependency(id="d5", org_id=org.id, source_id=sys_db_primary.id, target_id=sys_db_replica.id, dep_type=DependencyType.DATA_SYNC),
        Dependency(id="d6", org_id=org.id, source_id=sys_db_primary.id, target_id=sys_backup.id, dep_type=DependencyType.DATA_SYNC),
    ]
    for dep in deps:
        dep_repo.save(dep)

    # Recovery Strategies
    strat_restore = RecoveryStrategy(
        id="strat-restore", name="Restore from Backup", strategy_type=StrategyType.BACKUP_RESTORE,
        optimistic_hours=2.0, likely_hours=4.0, pessimistic_hours=8.0, resource_cost=2.0
    )
    strat_failover = RecoveryStrategy(
        id="strat-failover", name="Failover to Replica", strategy_type=StrategyType.FAILOVER,
        optimistic_hours=0.5, likely_hours=1.0, pessimistic_hours=2.0, resource_cost=1.0
    )
    strat_repo.save(strat_restore)
    strat_repo.save(strat_failover)

    # Scenarios
    scenario = DisasterScenario(
        id="scen-db-fail", name="Primary Database Failure", category=DisasterCategory.DATABASE_FAILURE,
        affected_systems=[AffectedSystem(system_id="sys-db-pri", health_impact=1.0)]
    )
    scenario_repo.save(scenario)


def _init_simulation_engine():
    """Constructs the SimulationEngine from DB state and saves it to session."""
    db: SQLiteManager = st.session_state["db"]
    orgs = OrganizationRepository(db).list_all()
    if not orgs:
        return
    org = orgs[0]

    systems = SystemRepository(db).list_by_org(org.id)
    deps = DependencyRepository(db).list_by_org(org.id)
    services = BusinessServiceRepository(db).list_by_org(org.id)

    # Hardcoding the map for the demo
    svc_map = {
        "svc-payment": ["sys-app", "sys-db-pri"],
        "svc-portal": ["sys-igw", "sys-fw", "sys-app", "sys-db-pri", "sys-cache"],
        "svc-report": ["sys-db-rep"]
    }

    graph = DependencyGraph()
    for sys in systems:
        graph.add_system(sys)
    for dep in deps:
        graph.add_dependency(dep)

    # Currently active scenario
    scenario = DisasterScenarioRepository(db).get("scen-db-fail")
    if not scenario:
        # Fallback if somehow not loaded (should not happen if loaded correctly)
        scenario = DisasterScenario(
            id="scen-db-fail", name="Primary Database Failure", category=DisasterCategory.DATABASE_FAILURE,
            affected_systems=[AffectedSystem(system_id="sys-db-pri", health_impact=1.0)]
        )
    
    run_data = SimulationRun(org_id=org.id, scenario_id=scenario.id, rng_seed=42)
    pool = ResourcePool(team_capacity=5, budget_remaining=50000.0)

    engine = SimulationEngine(
        run_data=run_data,
        dep_graph=graph,
        services=services,
        service_systems_map=svc_map,
        resource_pool=pool
    )
    
    st.session_state["engine"] = engine
    st.session_state["active_scenario"] = scenario
    st.session_state["recovery_strategies"] = RecoveryStrategyRepository(db).list_all()

import json
from app.database.repositories import SimulationRunRepository

def save_current_run(engine: SimulationEngine):
    """Serialize the canonical run details to SQLite."""
    db: SQLiteManager = st.session_state["db"]
    run_repo = SimulationRunRepository(db)
    
    # 1. State Snapshot
    state_snapshot = {
        "systems": {
            sys_id: {"effective_availability": state.effective_availability}
            for sys_id, state in engine.system_states.items()
        },
        "services": []
    }
    for svc in engine.services:
        impact = engine.bia.get_impact(svc.id)
        if impact:
            state_snapshot["services"].append({
                "service_id": svc.id,
                "name": svc.name,
                "downtime_hours": impact.downtime_hours,
                "revenue_lost": impact.revenue_lost,
                "mtpd_breached": impact.mtpd_breached,
                "rto_target": svc.rto_hours
            })
            
    # 2. Event Ledger
    ledger = [
        {"category": e.category.value, "delta": e.delta, "reason": e.reason, "time": e.event_time}
        for e in engine.scoring.get_ledger()
    ]
    
    # 3. Serialize and save to local SQLite FIRST
    engine.run_data.state_snapshot_json = json.dumps(state_snapshot)
    engine.run_data.event_ledger_json = json.dumps(ledger)
    engine.run_data.schema_version = "1.0"
    
    run_repo.save(engine.run_data)
    
    # 4. Attempt optional GCS export
    try:
        exporter = GCPExporter()
        success = exporter.export_simulation_run(engine.run_data)
        if not success:
            st.warning("Simulation saved locally, but Cloud Storage export failed. See logs for details.", icon="⚠️")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"GCS export integration failed: {e}")
    
    
def load_historical_run(run_id: str) -> Optional[SimulationRun]:
    """Load a historical run for read-only viewing."""
    db: SQLiteManager = st.session_state["db"]
    run_repo = SimulationRunRepository(db)
    return run_repo.get(run_id)
