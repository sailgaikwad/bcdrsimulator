-- BCDR Simulator — SQLite Schema
-- This is the authoritative source of truth for all application data.
-- Google Cloud is additive only; this database must work standalone.

-- Core entities

CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS business_services (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL REFERENCES organizations(id),
    name TEXT NOT NULL,
    criticality INTEGER CHECK(criticality BETWEEN 1 AND 10),
    rto_hours REAL,
    rpo_hours REAL,
    mtpd_hours REAL,
    revenue_per_hour REAL DEFAULT 0.0,
    sla_penalty_per_hour REAL DEFAULT 0.0,
    reputation_decay_rate REAL DEFAULT 0.0,
    notification_deadline_hours REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS systems (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL REFERENCES organizations(id),
    name TEXT NOT NULL,
    system_type TEXT NOT NULL,
    tier TEXT DEFAULT 'standard',
    base_health REAL DEFAULT 1.0,
    recovery_priority INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dependencies (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL REFERENCES organizations(id),
    source_id TEXT NOT NULL REFERENCES systems(id),
    target_id TEXT NOT NULL REFERENCES systems(id),
    dep_type TEXT NOT NULL CHECK(dep_type IN ('hard', 'soft')),
    weight REAL DEFAULT 1.0 CHECK(weight BETWEEN 0.0 AND 1.0),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_service_map (
    system_id TEXT NOT NULL REFERENCES systems(id),
    service_id TEXT NOT NULL REFERENCES business_services(id),
    criticality_weight REAL DEFAULT 1.0,
    PRIMARY KEY (system_id, service_id)
);

-- Disaster scenario definitions

CREATE TABLE IF NOT EXISTS scenarios (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    severity REAL CHECK(severity BETWEEN 0.0 AND 1.0),
    affected_system_types TEXT,
    initial_health_impact REAL,
    propagation_probability REAL,
    scenario_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recovery strategies (templates)

CREATE TABLE IF NOT EXISTS recovery_strategies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    strategy_type TEXT NOT NULL,
    optimistic_hours REAL NOT NULL,
    likely_hours REAL NOT NULL,
    pessimistic_hours REAL NOT NULL,
    resource_cost REAL DEFAULT 0.0,
    data_loss_hours REAL DEFAULT 0.0,
    monetary_cost REAL DEFAULT 0.0,
    risk_reduction REAL DEFAULT 0.0,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Simulation runs

CREATE TABLE IF NOT EXISTS simulation_runs (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL REFERENCES organizations(id),
    scenario_id TEXT NOT NULL REFERENCES scenarios(id),
    rng_seed INTEGER NOT NULL,
    status TEXT DEFAULT 'created',
    start_time REAL,
    end_time REAL,
    total_downtime_hours REAL,
    final_resilience_score REAL,
    final_risk_level TEXT,
    decisions_json TEXT,
    config_json TEXT,
    schema_version TEXT DEFAULT '1.0',
    state_snapshot_json TEXT,
    event_ledger_json TEXT,
    timeline_json TEXT,
    team_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Simulation event log

CREATE TABLE IF NOT EXISTS simulation_events (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES simulation_runs(id),
    event_type TEXT NOT NULL,
    event_time REAL NOT NULL,
    system_id TEXT,
    description TEXT,
    details_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Failure events

CREATE TABLE IF NOT EXISTS failure_events (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES simulation_runs(id),
    system_id TEXT NOT NULL REFERENCES systems(id),
    event_time REAL NOT NULL,
    failure_type TEXT NOT NULL,
    health_before REAL,
    health_after REAL,
    is_propagated INTEGER DEFAULT 0,
    source_failure_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recovery events

CREATE TABLE IF NOT EXISTS recovery_events (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES simulation_runs(id),
    system_id TEXT NOT NULL REFERENCES systems(id),
    strategy_id TEXT REFERENCES recovery_strategies(id),
    decision_time REAL,
    start_time REAL,
    completion_time REAL,
    planned_duration REAL,
    actual_duration REAL,
    health_restored REAL,
    resources_used REAL,
    cost REAL,
    success INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Score ledger

CREATE TABLE IF NOT EXISTS score_events (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES simulation_runs(id),
    decision_id TEXT,
    category TEXT NOT NULL,
    delta REAL NOT NULL,
    reason TEXT NOT NULL,
    event_time REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hidden facts (investigation/uncertainty mechanic)

CREATE TABLE IF NOT EXISTS hidden_facts (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES simulation_runs(id),
    fact_key TEXT NOT NULL,
    true_value REAL NOT NULL,
    revealed_low REAL,
    revealed_high REAL,
    confidence REAL DEFAULT 0.0 CHECK(confidence BETWEEN 0.0 AND 1.0),
    investigated INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Decisions log

CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES simulation_runs(id),
    decision_time REAL NOT NULL,
    decision_type TEXT NOT NULL,
    choice TEXT NOT NULL,
    alternatives_json TEXT,
    rationale TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Risk assessments

CREATE TABLE IF NOT EXISTS risk_assessments (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES simulation_runs(id),
    system_id TEXT REFERENCES systems(id),
    assessment_time REAL,
    probability REAL,
    impact REAL,
    exposure REAL,
    risk_score REAL,
    risk_level TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- BIA assessments

CREATE TABLE IF NOT EXISTS bia_assessments (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES simulation_runs(id),
    service_id TEXT NOT NULL REFERENCES business_services(id),
    assessment_time REAL,
    criticality_score INTEGER,
    revenue_impact REAL,
    sla_impact REAL,
    reputation_impact REAL,
    mtpd_breached INTEGER DEFAULT 0,
    wrt_hours REAL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cloud export tracking

CREATE TABLE IF NOT EXISTS cloud_exports (
    id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES simulation_runs(id),
    export_type TEXT NOT NULL,
    destination TEXT,
    status TEXT DEFAULT 'pending',
    exported_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes

CREATE INDEX IF NOT EXISTS idx_deps_source ON dependencies(source_id);
CREATE INDEX IF NOT EXISTS idx_deps_target ON dependencies(target_id);
CREATE INDEX IF NOT EXISTS idx_sim_events_run ON simulation_events(run_id);
CREATE INDEX IF NOT EXISTS idx_sim_events_time ON simulation_events(run_id, event_time);
CREATE INDEX IF NOT EXISTS idx_failure_events_run ON failure_events(run_id);
CREATE INDEX IF NOT EXISTS idx_recovery_events_run ON recovery_events(run_id);
CREATE INDEX IF NOT EXISTS idx_score_events_run ON score_events(run_id);
CREATE INDEX IF NOT EXISTS idx_hidden_facts_run ON hidden_facts(run_id);
CREATE INDEX IF NOT EXISTS idx_decisions_run ON decisions(run_id);
CREATE INDEX IF NOT EXISTS idx_risk_run ON risk_assessments(run_id);
CREATE INDEX IF NOT EXISTS idx_bia_run ON bia_assessments(run_id);
CREATE INDEX IF NOT EXISTS idx_services_org ON business_services(org_id);
CREATE INDEX IF NOT EXISTS idx_systems_org ON systems(org_id);
CREATE INDEX IF NOT EXISTS idx_runs_org ON simulation_runs(org_id);
