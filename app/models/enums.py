"""
Shared enumerations and base types for the BCDR Simulator domain model.

These enums map directly to BC/DR industry terminology (BIA, RTO, RPO, MTPD, etc.)
and are used across models, engines, and the database layer.
"""

from enum import Enum


class SystemType(str, Enum):
    """Infrastructure system classification."""
    SERVER = "server"
    DATABASE = "database"
    NETWORK = "network"
    STORAGE = "storage"
    APPLICATION = "application"
    FIREWALL = "firewall"
    CACHE = "cache"
    LOAD_BALANCER = "load_balancer"
    GATEWAY = "gateway"
    BACKUP = "backup"


class SystemTier(str, Enum):
    """System criticality tier."""
    CRITICAL = "critical"
    STANDARD = "standard"
    AUXILIARY = "auxiliary"


class SystemStatus(str, Enum):
    """Runtime status of a system during simulation."""
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"
    RESTORED = "restored"


class DependencyType(str, Enum):
    """
    Dependency classification.

    HARD: Service operation strongly depends on the upstream system.
          If upstream fails, downstream is severely impacted.
    SOFT: Service can degrade without the upstream system but
          continues to operate at reduced capacity.
    """
    HARD = "hard"
    SOFT = "soft"
    DATA_SYNC = "data_sync"


class StrategyType(str, Enum):
    """Recovery strategy classification."""
    BACKUP_RESTORE = "backup_restore"
    LOCAL_BACKUP = "local_backup"
    FAILOVER = "failover"
    HOT_STANDBY = "hot_standby"
    WARM_STANDBY = "warm_standby"
    COLD_STANDBY = "cold_standby"
    CLOUD_RECOVERY = "cloud_recovery"
    MANUAL_RECOVERY = "manual_recovery"
    REDUNDANCY = "redundancy"


class RiskLevel(str, Enum):
    """Risk severity classification based on P × I × E score."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @classmethod
    def from_score(cls, score: float) -> "RiskLevel":
        """
        Map a normalized risk score (0.0–1.0) to a risk level.

        Thresholds:
            0.0–0.2  → LOW
            0.2–0.5  → MEDIUM
            0.5–0.8  → HIGH
            0.8–1.0  → CRITICAL
        """
        if score < 0.2:
            return cls.LOW
        elif score < 0.5:
            return cls.MEDIUM
        elif score < 0.8:
            return cls.HIGH
        else:
            return cls.CRITICAL


class ScoreCategory(str, Enum):
    """Resilience score dimensions for the score ledger."""
    RECOVERY_PERFORMANCE = "recovery_performance"
    DATA_PROTECTION = "data_protection"
    BUSINESS_AVAILABILITY = "business_availability"
    RESOURCE_EFFICIENCY = "resource_efficiency"
    COST_EFFICIENCY = "cost_efficiency"


class EventType(str, Enum):
    """Discrete-event simulation event types."""
    FAILURE = "failure"
    DEGRADATION = "degradation"
    PROPAGATION = "propagation"
    INVESTIGATION_COMPLETE = "investigation_complete"
    RECOVERY_START = "recovery_start"
    RECOVERY_COMPLETE = "recovery_complete"
    DECISION_DEADLINE = "decision_deadline"
    COMMUNICATION = "communication"
    DATA_RESTORE = "data_restore"
    BACKLOG_RECOVERY = "backlog_recovery"
    MTPD_BREACH = "mtpd_breach"
    SLA_VIOLATION = "sla_violation"


class SimulationStatus(str, Enum):
    """Lifecycle status of a simulation run."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class DisasterCategory(str, Enum):
    """Classification of disaster scenarios."""
    SERVER_FAILURE = "server_failure"
    DATABASE_FAILURE = "database_failure"
    NETWORK_OUTAGE = "network_outage"
    DATACENTER_OUTAGE = "datacenter_outage"
    CLOUD_REGION_OUTAGE = "cloud_region_outage"
    POWER_FAILURE = "power_failure"
    RANSOMWARE = "ransomware"
    DATA_CORRUPTION = "data_corruption"
    CYBERATTACK = "cyberattack"
    CLOUD_SERVICE_OUTAGE = "cloud_service_outage"
    SUPPLY_CHAIN = "supply_chain"
