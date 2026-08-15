"""
FinServe Demo Integration Scenario.

This script sets up the FinServe Demo dataset as described in the Prompt,
runs a full headless simulation, and generates a Recovery Report.
"""

import os
import random
from app.database.sqlite_manager import SQLiteManager
from app.database.repositories import (
    OrganizationRepository, BusinessServiceRepository, SystemRepository,
    DependencyRepository, RecoveryStrategyRepository, SimulationRunRepository
)
from app.models.organization import Organization, BusinessService
from app.models.system import System, SystemState
from app.models.dependency import Dependency
from app.models.recovery import RecoveryStrategy
from app.models.simulation import SimulationRun, ResourcePool
from app.models.enums import SystemType, DependencyType, StrategyType, DisasterCategory
from app.models.disaster import DisasterScenario, AffectedSystem
from app.graph.dependency_graph import DependencyGraph
from app.core.simulation_engine import SimulationEngine

def run_demo():
    print("=== FinServe Demo Scenario ===")
    
    # 1. Initialize DB (in-memory for this run, but we can also use a file)
    db = SQLiteManager(":memory:")
    db.initialize()

    # 2. Setup Data
    org_repo = OrganizationRepository(db)
    svc_repo = BusinessServiceRepository(db)
    sys_repo = SystemRepository(db)
    dep_repo = DependencyRepository(db)
    strat_repo = RecoveryStrategyRepository(db)
    
    org = Organization(id="org-finserve", name="FinServe Demo", industry="Finance")
    org_repo.save(org)

    print(f"Created Organization: {org.name}")

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

    print(f"Created {len(systems)} Systems")

    # Dependencies (Topological)
    deps = [
        Dependency(id="d1", org_id=org.id, source_id=sys_igw.id, target_id=sys_fw.id, dep_type=DependencyType.HARD),
        Dependency(id="d2", org_id=org.id, source_id=sys_fw.id, target_id=sys_app.id, dep_type=DependencyType.HARD),
        Dependency(id="d3", org_id=org.id, source_id=sys_app.id, target_id=sys_db_primary.id, dep_type=DependencyType.HARD),
        Dependency(id="d4", org_id=org.id, source_id=sys_app.id, target_id=sys_cache.id, dep_type=DependencyType.SOFT, weight=0.3),
        Dependency(id="d5", org_id=org.id, source_id=sys_db_primary.id, target_id=sys_db_replica.id, dep_type=DependencyType.HARD),
        Dependency(id="d6", org_id=org.id, source_id=sys_db_primary.id, target_id=sys_backup.id, dep_type=DependencyType.SOFT, weight=0.1),
    ]
    for dep in deps:
        dep_repo.save(dep)

    print("Created Dependency Graph")

    # Service Mapping
    svc_map = {
        svc_payment.id: [sys_app.id, sys_db_primary.id],
        svc_portal.id: [sys_igw.id, sys_fw.id, sys_app.id, sys_db_primary.id, sys_cache.id],
        svc_report.id: [sys_db_replica.id]
    }

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

    # 3. Build Graph
    graph = DependencyGraph()
    for sys in systems:
        graph.add_system(sys)
    for dep in deps:
        graph.add_dependency(dep)
        
    print(f"Topological order: {graph.get_topological_order()}")

    # 4. Scenario & Run Setup
    scenario = DisasterScenario(
        id="scen-db-fail", name="Primary Database Failure", category=DisasterCategory.DATABASE_FAILURE,
        affected_systems=[AffectedSystem(system_id=sys_db_primary.id, health_impact=1.0)]
    )
    
    run_data = SimulationRun(id="run-demo-1", org_id=org.id, scenario_id=scenario.id, rng_seed=42)
    pool = ResourcePool(team_capacity=5, budget_remaining=50000.0)
    
    engine = SimulationEngine(
        run_data=run_data,
        dep_graph=graph,
        services=[svc_payment, svc_portal, svc_report],
        service_systems_map=svc_map,
        resource_pool=pool
    )

    # 5. Trigger Disaster
    print("\n--- Triggering Disaster ---")
    print(f"Scenario: {scenario.name}")
    engine.trigger_disaster({sys_db_primary.id: 1.0})

    # Step exactly 1 hour, then make a decision
    while not engine.events.is_empty() and engine.current_time < 1.0:
        evt = engine.step()
        if evt:
            print(f"T={evt.time:.2f} | {evt.event_type.name} | {evt.description}")

    print("\n--- Making Recovery Decision (T=1.0) ---")
    print("Decision: Restore from Backup")
    
    # Trigger recovery action
    plan, rec_evt = engine.recovery.start_recovery(sys_db_primary.id, strat_restore, engine.current_time)
    if plan:
        print(f"Recovery plan accepted. Sampled duration: {plan.actual_duration:.2f}h")
        engine.schedule_event(rec_evt)
    else:
        print("Recovery plan rejected (resource constraints)")

    # 6. Run to completion
    print("\n--- Continuing Simulation ---")
    engine.run_until_empty()

    # 7. Print Report
    print("\n=== RECOVERY REPORT ===")
    print(f"Simulation Status: {engine.run_data.status.value}")
    print(f"Total simulated time: {engine.current_time:.2f} hours")
    print(f"Final Composite Resilience Score: {engine.scoring.get_composite_score():.1f}/100")
    
    print("\nScore Ledger:")
    for evt in engine.scoring.get_ledger():
        print(f"  [{evt.category.value}] {evt.delta:+.1f}: {evt.reason}")
        
    print("\nBusiness Service Impacts:")
    for svc in engine.services:
        impact = engine.bia.get_impact(svc.id)
        if impact:
            mtpd_breach = "YES" if impact.mtpd_breached else "NO"
            print(f"  {svc.name}: MTPD Breached={mtpd_breach}, Revenue Lost=INR {impact.revenue_lost:,.2f}, Downtime={impact.downtime_hours:.2f}h")

    # 8. Save the run to GCS directly to test export
    from app.cloud.gcp_exporter import GCPExporter
    print("\n--- Exporting Run to GCS ---")
    
    exporter = GCPExporter()
    success = exporter.export_simulation_run(engine.run_data)
    if success:
        print("Run exported to GCS successfully.")
    else:
        print("Run export to GCS failed.")

if __name__ == "__main__":
    run_demo()
