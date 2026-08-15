"""
Tests for SQLite database layer — schema initialization,
CRUD operations via repositories, and data integrity.
"""

import pytest
from app.database.sqlite_manager import SQLiteManager
from app.database.repositories import (
    OrganizationRepository,
    BusinessServiceRepository,
    SystemRepository,
    DependencyRepository,
    SimulationRunRepository,
    ScoreEventRepository,
    HiddenFactRepository,
    RecoveryStrategyRepository,
)
from app.models.organization import Organization, BusinessService
from app.models.system import System
from app.models.dependency import Dependency
from app.models.recovery import RecoveryStrategy
from app.models.simulation import SimulationRun, ScoreEvent, HiddenFact
from app.models.enums import (
    SystemType, DependencyType, StrategyType,
    ScoreCategory, SimulationStatus,
)


@pytest.fixture
def db():
    """In-memory SQLite database for testing."""
    manager = SQLiteManager(":memory:")
    manager.initialize()
    return manager


@pytest.fixture
def org(db):
    """Pre-saved test organization."""
    repo = OrganizationRepository(db)
    org = Organization(id="org-test", name="Test Corp", industry="Technology")
    repo.save(org)
    return org


# ── Schema initialization ──────────────────────────────────────────

class TestSchemaInit:
    def test_tables_created(self, db):
        expected_tables = [
            "organizations", "business_services", "systems", "dependencies",
            "system_service_map", "scenarios", "recovery_strategies",
            "simulation_runs", "simulation_events", "failure_events",
            "recovery_events", "score_events", "hidden_facts",
            "decisions", "risk_assessments", "bia_assessments", "cloud_exports",
        ]
        for table in expected_tables:
            assert db.table_exists(table), f"Table {table} should exist"

    def test_idempotent_init(self, db):
        """Calling initialize() twice should not raise."""
        db.initialize()
        db.initialize()
        assert db.table_exists("organizations")


# ── OrganizationRepository ──────────────────────────────────────────

class TestOrganizationRepo:
    def test_save_and_get(self, db):
        repo = OrganizationRepository(db)
        org = Organization(id="org-1", name="FinServe", industry="Finance")
        repo.save(org)

        loaded = repo.get("org-1")
        assert loaded is not None
        assert loaded.name == "FinServe"
        assert loaded.industry == "Finance"

    def test_get_nonexistent(self, db):
        repo = OrganizationRepository(db)
        assert repo.get("no-such-org") is None

    def test_list_all(self, db):
        repo = OrganizationRepository(db)
        repo.save(Organization(id="a", name="Alpha"))
        repo.save(Organization(id="b", name="Beta"))
        orgs = repo.list_all()
        assert len(orgs) == 2

    def test_delete(self, db):
        repo = OrganizationRepository(db)
        repo.save(Organization(id="del-1", name="Delete Me"))
        repo.delete("del-1")
        assert repo.get("del-1") is None


# ── BusinessServiceRepository ──────────────────────────────────────

class TestBusinessServiceRepo:
    def test_save_and_get(self, db, org):
        repo = BusinessServiceRepository(db)
        svc = BusinessService(
            id="svc-1", org_id=org.id, name="Payment Processing",
            criticality=9, rto_hours=2.0, rpo_hours=0.5, mtpd_hours=8.0,
            revenue_per_hour=10000.0,
        )
        repo.save(svc)

        loaded = repo.get("svc-1")
        assert loaded is not None
        assert loaded.name == "Payment Processing"
        assert loaded.criticality == 9
        assert loaded.revenue_per_hour == 10000.0

    def test_list_by_org(self, db, org):
        repo = BusinessServiceRepository(db)
        repo.save(BusinessService(id="s1", org_id=org.id, name="A", criticality=5))
        repo.save(BusinessService(id="s2", org_id=org.id, name="B", criticality=9))
        services = repo.list_by_org(org.id)
        assert len(services) == 2
        # Should be ordered by criticality DESC
        assert services[0].criticality >= services[1].criticality


# ── SystemRepository ────────────────────────────────────────────────

class TestSystemRepo:
    def test_save_and_get(self, db, org):
        repo = SystemRepository(db)
        sys = System(
            id="sys-1", org_id=org.id, name="Primary DB",
            system_type=SystemType.DATABASE,
        )
        repo.save(sys)

        loaded = repo.get("sys-1")
        assert loaded is not None
        assert loaded.name == "Primary DB"
        assert loaded.system_type == SystemType.DATABASE

    def test_list_by_org(self, db, org):
        repo = SystemRepository(db)
        repo.save(System(id="s1", org_id=org.id, name="A", system_type=SystemType.SERVER))
        repo.save(System(id="s2", org_id=org.id, name="B", system_type=SystemType.DATABASE))
        systems = repo.list_by_org(org.id)
        assert len(systems) == 2


# ── DependencyRepository ───────────────────────────────────────────

class TestDependencyRepo:
    def test_save_and_list(self, db, org):
        sys_repo = SystemRepository(db)
        sys_repo.save(System(id="s1", org_id=org.id, name="A", system_type=SystemType.SERVER))
        sys_repo.save(System(id="s2", org_id=org.id, name="B", system_type=SystemType.DATABASE))

        dep_repo = DependencyRepository(db)
        dep = Dependency(
            id="d1", org_id=org.id, source_id="s1", target_id="s2",
            dep_type=DependencyType.HARD, weight=0.8,
        )
        dep_repo.save(dep)

        deps = dep_repo.list_by_org(org.id)
        assert len(deps) == 1
        assert deps[0].weight == 0.8
        assert deps[0].dep_type == DependencyType.HARD


# ── ScoreEventRepository ───────────────────────────────────────────

class TestScoreEventRepo:
    def test_save_and_list(self, db, org):
        # Insert a scenario first (FK requirement)
        with db.connection() as conn:
            conn.execute(
                "INSERT INTO scenarios (id, name, category) VALUES (?, ?, ?)",
                ("scen-1", "Test Scenario", "database_failure"),
            )

        # Need a simulation run first
        run_repo = SimulationRunRepository(db)
        run = SimulationRun(
            id="run-1", org_id=org.id, scenario_id="scen-1", rng_seed=42,
        )
        run_repo.save(run)

        score_repo = ScoreEventRepository(db)
        score_repo.save(ScoreEvent(
            id="se-1", run_id="run-1",
            category=ScoreCategory.RECOVERY_PERFORMANCE,
            delta=-10.0, reason="RTO exceeded by 2 hours",
            event_time=3.0,
        ))
        score_repo.save(ScoreEvent(
            id="se-2", run_id="run-1",
            category=ScoreCategory.DATA_PROTECTION,
            delta=5.0, reason="Backup restored within RPO",
            event_time=4.0,
        ))

        events = score_repo.list_by_run("run-1")
        assert len(events) == 2
        assert events[0].event_time <= events[1].event_time


# ── RecoveryStrategyRepository ──────────────────────────────────────

class TestRecoveryStrategyRepo:
    def test_save_and_list(self, db):
        repo = RecoveryStrategyRepository(db)
        strat = RecoveryStrategy(
            id="rs-1", name="Hot Standby",
            strategy_type=StrategyType.HOT_STANDBY,
            optimistic_hours=0.25, likely_hours=0.5, pessimistic_hours=1.0,
            resource_cost=2.0, monetary_cost=5000.0,
        )
        repo.save(strat)

        loaded = repo.get("rs-1")
        assert loaded is not None
        assert loaded.name == "Hot Standby"
        assert loaded.monetary_cost == 5000.0

        all_strats = repo.list_all()
        assert len(all_strats) == 1
