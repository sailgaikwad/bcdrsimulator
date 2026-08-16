"""
Repository layer for CRUD operations on domain entities.

Each repository provides type-safe persistence using Pydantic models
and the SQLiteManager connection interface.
"""

import json
from typing import Optional

from app.database.sqlite_manager import SQLiteManager
from app.models.organization import Organization, BusinessService
from app.models.system import System
from app.models.dependency import Dependency
from app.models.disaster import DisasterScenario
from app.models.recovery import RecoveryStrategy
from app.models.simulation import (
    SimulationRun,
    ScoreEvent,
    HiddenFact,
    RiskAssessment,
)


class OrganizationRepository:
    """CRUD operations for organizations."""

    def __init__(self, db: SQLiteManager):
        self.db = db

    def save(self, org: Organization) -> None:
        with self.db.connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO organizations (id, name, industry) VALUES (?, ?, ?)",
                (org.id, org.name, org.industry),
            )

    def get(self, org_id: str) -> Optional[Organization]:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM organizations WHERE id = ?", (org_id,)
            ).fetchone()
            if row is None:
                return None
            return Organization(id=row["id"], name=row["name"], industry=row["industry"])

    def list_all(self) -> list[Organization]:
        with self.db.connection() as conn:
            rows = conn.execute("SELECT * FROM organizations ORDER BY name").fetchall()
            return [
                Organization(id=r["id"], name=r["name"], industry=r["industry"])
                for r in rows
            ]

    def delete(self, org_id: str) -> None:
        with self.db.connection() as conn:
            conn.execute("DELETE FROM organizations WHERE id = ?", (org_id,))


class BusinessServiceRepository:
    """CRUD operations for business services."""

    def __init__(self, db: SQLiteManager):
        self.db = db

    def save(self, svc: BusinessService) -> None:
        with self.db.connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO business_services
                   (id, org_id, name, criticality, rto_hours, rpo_hours, mtpd_hours,
                    revenue_per_hour, sla_penalty_per_hour, reputation_decay_rate,
                    notification_deadline_hours)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    svc.id, svc.org_id, svc.name, svc.criticality,
                    svc.rto_hours, svc.rpo_hours, svc.mtpd_hours,
                    svc.revenue_per_hour, svc.sla_penalty_per_hour,
                    svc.reputation_decay_rate, svc.notification_deadline_hours,
                ),
            )

    def get(self, service_id: str) -> Optional[BusinessService]:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM business_services WHERE id = ?", (service_id,)
            ).fetchone()
            if row is None:
                return None
            return BusinessService(
                id=row["id"], org_id=row["org_id"], name=row["name"],
                criticality=row["criticality"], rto_hours=row["rto_hours"],
                rpo_hours=row["rpo_hours"], mtpd_hours=row["mtpd_hours"],
                revenue_per_hour=row["revenue_per_hour"],
                sla_penalty_per_hour=row["sla_penalty_per_hour"],
                reputation_decay_rate=row["reputation_decay_rate"],
                notification_deadline_hours=row["notification_deadline_hours"],
            )

    def list_by_org(self, org_id: str) -> list[BusinessService]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM business_services WHERE org_id = ? ORDER BY criticality DESC",
                (org_id,),
            ).fetchall()
            return [
                BusinessService(
                    id=r["id"], org_id=r["org_id"], name=r["name"],
                    criticality=r["criticality"], rto_hours=r["rto_hours"],
                    rpo_hours=r["rpo_hours"], mtpd_hours=r["mtpd_hours"],
                    revenue_per_hour=r["revenue_per_hour"],
                    sla_penalty_per_hour=r["sla_penalty_per_hour"],
                    reputation_decay_rate=r["reputation_decay_rate"],
                    notification_deadline_hours=r["notification_deadline_hours"],
                )
                for r in rows
            ]


class SystemRepository:
    """CRUD operations for infrastructure systems."""

    def __init__(self, db: SQLiteManager):
        self.db = db

    def save(self, system: System) -> None:
        with self.db.connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO systems
                   (id, org_id, name, system_type, tier, base_health, recovery_priority)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    system.id, system.org_id, system.name,
                    system.system_type.value, system.tier.value,
                    system.base_health, system.recovery_priority,
                ),
            )

    def get(self, system_id: str) -> Optional[System]:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM systems WHERE id = ?", (system_id,)
            ).fetchone()
            if row is None:
                return None
            return System(
                id=row["id"], org_id=row["org_id"], name=row["name"],
                system_type=row["system_type"], tier=row["tier"],
                base_health=row["base_health"],
                recovery_priority=row["recovery_priority"],
            )

    def list_by_org(self, org_id: str) -> list[System]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM systems WHERE org_id = ? ORDER BY recovery_priority",
                (org_id,),
            ).fetchall()
            return [
                System(
                    id=r["id"], org_id=r["org_id"], name=r["name"],
                    system_type=r["system_type"], tier=r["tier"],
                    base_health=r["base_health"],
                    recovery_priority=r["recovery_priority"],
                )
                for r in rows
            ]


class DependencyRepository:
    """CRUD operations for dependency edges."""

    def __init__(self, db: SQLiteManager):
        self.db = db

    def save(self, dep: Dependency) -> None:
        with self.db.connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO dependencies
                   (id, org_id, source_id, target_id, dep_type, weight, description)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    dep.id, dep.org_id, dep.source_id, dep.target_id,
                    dep.dep_type.value, dep.weight, dep.description,
                ),
            )

    def list_by_org(self, org_id: str) -> list[Dependency]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM dependencies WHERE org_id = ?", (org_id,)
            ).fetchall()
            return [
                Dependency(
                    id=r["id"], org_id=r["org_id"],
                    source_id=r["source_id"], target_id=r["target_id"],
                    dep_type=r["dep_type"], weight=r["weight"],
                    description=r["description"],
                )
                for r in rows
            ]

    def delete(self, dep_id: str) -> None:
        with self.db.connection() as conn:
            conn.execute("DELETE FROM dependencies WHERE id = ?", (dep_id,))


class SimulationRunRepository:
    """CRUD operations for simulation runs."""

    def __init__(self, db: SQLiteManager):
        self.db = db

    def save(self, run: SimulationRun) -> None:
        with self.db.connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO simulation_runs
                   (id, org_id, scenario_id, rng_seed, status, start_time, end_time,
                    total_downtime_hours, final_resilience_score, final_risk_level,
                    decisions_json, config_json, schema_version, state_snapshot_json,
                    event_ledger_json, timeline_json, team_id, completed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run.id, run.org_id, run.scenario_id, run.rng_seed,
                    run.status.value, run.start_time, run.end_time,
                    run.total_downtime_hours, run.final_resilience_score,
                    run.final_risk_level.value if run.final_risk_level else None,
                    run.decisions_json, run.config_json, run.schema_version,
                    run.state_snapshot_json, run.event_ledger_json, run.timeline_json,
                    run.team_id, None,
                ),
            )

    def get(self, run_id: str) -> Optional[SimulationRun]:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM simulation_runs WHERE id = ?", (run_id,)
            ).fetchone()
            if row is None:
                return None
            return SimulationRun(
                id=row["id"], org_id=row["org_id"],
                scenario_id=row["scenario_id"], rng_seed=row["rng_seed"],
                status=row["status"], start_time=row["start_time"],
                end_time=row["end_time"],
                total_downtime_hours=row["total_downtime_hours"],
                final_resilience_score=row["final_resilience_score"],
                final_risk_level=row["final_risk_level"],
                decisions_json=row["decisions_json"],
                config_json=row["config_json"],
                schema_version=row["schema_version"],
                state_snapshot_json=row["state_snapshot_json"],
                event_ledger_json=row["event_ledger_json"],
                timeline_json=row["timeline_json"],
                team_id=row["team_id"],
            )

    def list_by_org(self, org_id: str, limit: int = 50) -> list[SimulationRun]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM simulation_runs WHERE org_id = ? ORDER BY created_at DESC LIMIT ?",
                (org_id, limit),
            ).fetchall()
            return [
                SimulationRun(
                    id=r["id"], org_id=r["org_id"],
                    scenario_id=r["scenario_id"], rng_seed=r["rng_seed"],
                    status=r["status"], start_time=r["start_time"],
                    end_time=r["end_time"],
                    total_downtime_hours=r["total_downtime_hours"],
                    final_resilience_score=r["final_resilience_score"],
                    final_risk_level=r["final_risk_level"],
                    decisions_json=r["decisions_json"],
                    config_json=r["config_json"],
                    schema_version=r["schema_version"],
                    state_snapshot_json=r["state_snapshot_json"],
                    event_ledger_json=r["event_ledger_json"],
                    timeline_json=r["timeline_json"],
                    team_id=r["team_id"],
                )
                for r in rows
            ]


class ScoreEventRepository:
    """CRUD operations for score ledger entries."""

    def __init__(self, db: SQLiteManager):
        self.db = db

    def save(self, event: ScoreEvent) -> None:
        with self.db.connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO score_events
                   (id, run_id, decision_id, category, delta, reason, event_time)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    event.id, event.run_id, event.decision_id,
                    event.category.value, event.delta, event.reason,
                    event.event_time,
                ),
            )

    def list_by_run(self, run_id: str) -> list[ScoreEvent]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM score_events WHERE run_id = ? ORDER BY event_time",
                (run_id,),
            ).fetchall()
            return [
                ScoreEvent(
                    id=r["id"], run_id=r["run_id"],
                    decision_id=r["decision_id"], category=r["category"],
                    delta=r["delta"], reason=r["reason"],
                    event_time=r["event_time"],
                )
                for r in rows
            ]


class HiddenFactRepository:
    """CRUD operations for hidden facts (investigation mechanic)."""

    def __init__(self, db: SQLiteManager):
        self.db = db

    def save(self, fact: HiddenFact) -> None:
        with self.db.connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO hidden_facts
                   (id, run_id, fact_key, true_value, revealed_low, revealed_high,
                    confidence, investigated, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (
                    fact.id, fact.run_id, fact.fact_key, fact.true_value,
                    fact.revealed_low, fact.revealed_high, fact.confidence,
                    1 if fact.investigated else 0,
                ),
            )

    def list_by_run(self, run_id: str) -> list[HiddenFact]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM hidden_facts WHERE run_id = ? ORDER BY fact_key",
                (run_id,),
            ).fetchall()
            return [
                HiddenFact(
                    id=r["id"], run_id=r["run_id"], fact_key=r["fact_key"],
                    true_value=r["true_value"], revealed_low=r["revealed_low"],
                    revealed_high=r["revealed_high"], confidence=r["confidence"],
                    investigated=bool(r["investigated"]),
                )
                for r in rows
            ]


class RecoveryStrategyRepository:
    """CRUD operations for recovery strategy templates."""

    def __init__(self, db: SQLiteManager):
        self.db = db

    def save(self, strategy: RecoveryStrategy) -> None:
        with self.db.connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO recovery_strategies
                   (id, name, strategy_type, optimistic_hours, likely_hours,
                    pessimistic_hours, resource_cost, data_loss_hours,
                    monetary_cost, risk_reduction, description)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    strategy.id, strategy.name, strategy.strategy_type.value,
                    strategy.optimistic_hours, strategy.likely_hours,
                    strategy.pessimistic_hours, strategy.resource_cost,
                    strategy.data_loss_hours, strategy.monetary_cost,
                    strategy.risk_reduction, strategy.description,
                ),
            )

    def list_all(self) -> list[RecoveryStrategy]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM recovery_strategies ORDER BY name"
            ).fetchall()
            return [
                RecoveryStrategy(
                    id=r["id"], name=r["name"],
                    strategy_type=r["strategy_type"],
                    optimistic_hours=r["optimistic_hours"],
                    likely_hours=r["likely_hours"],
                    pessimistic_hours=r["pessimistic_hours"],
                    resource_cost=r["resource_cost"],
                    data_loss_hours=r["data_loss_hours"],
                    monetary_cost=r["monetary_cost"],
                    risk_reduction=r["risk_reduction"],
                    description=r["description"],
                )
                for r in rows
            ]

    def get(self, strategy_id: str) -> Optional[RecoveryStrategy]:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM recovery_strategies WHERE id = ?", (strategy_id,)
            ).fetchone()
            if row is None:
                return None
            return RecoveryStrategy(
                id=row["id"], name=row["name"],
                strategy_type=row["strategy_type"],
                optimistic_hours=row["optimistic_hours"],
                likely_hours=row["likely_hours"],
                pessimistic_hours=row["pessimistic_hours"],
                resource_cost=row["resource_cost"],
                data_loss_hours=row["data_loss_hours"],
                monetary_cost=row["monetary_cost"],
                risk_reduction=row["risk_reduction"],
                description=row["description"],
            )

class DisasterScenarioRepository:
    """CRUD operations for disaster scenarios."""

    def __init__(self, db: SQLiteManager):
        self.db = db

    def save(self, scenario: DisasterScenario) -> None:
        with self.db.connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO scenarios 
                (id, name, category, description, severity, propagation_probability, scenario_json) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scenario.id,
                    scenario.name,
                    scenario.category.value,
                    scenario.description,
                    scenario.severity,
                    scenario.propagation_probability,
                    scenario.model_dump_json(),
                ),
            )

    def get(self, scenario_id: str) -> Optional[DisasterScenario]:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM scenarios WHERE id = ?", (scenario_id,)
            ).fetchone()
            if row is None:
                return None
            import json
            data = json.loads(row["scenario_json"])
            return DisasterScenario(**data)

    def list_all(self) -> list[DisasterScenario]:
        with self.db.connection() as conn:
            rows = conn.execute("SELECT * FROM scenarios ORDER BY name").fetchall()
            import json
            scenarios = []
            for row in rows:
                data = json.loads(row["scenario_json"])
                scenarios.append(DisasterScenario(**data))
            return scenarios
