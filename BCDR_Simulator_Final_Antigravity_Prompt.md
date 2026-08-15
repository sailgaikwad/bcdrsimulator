# Antigravity Final Build Prompt — Adaptive Business Continuity & Disaster Recovery Simulator

You are my senior software architect, Python engineer, Google Cloud engineer, cybersecurity/data engineer, simulation engineer, and DevOps engineer.

Your job is to PLAN, BUILD, TEST, DOCUMENT, and locally validate a complete portfolio-quality application called:

**Adaptive Business Continuity & Disaster Recovery (BC/DR) Simulator**

This is a serious intermediate-to-advanced project for:
- cybersecurity internship preparation
- cloud engineering experience
- software engineering portfolio work
- research internship preparation
- practical Google Cloud experience
- demonstrating algorithms, simulation, data engineering, and resilient architecture

The project must be technically substantial, but not unnecessarily over-engineered. I must be able to explain every major component in an interview.

---

# 0. NON-NEGOTIABLE OPERATING RULES

## 0.1 Build before beautifying

Do not start by generating random files or a large UI mockup.

First inspect the existing workspace, understand what is already present, and produce an implementation plan.

Then build incrementally.

## 0.2 Local-first, cloud-enhanced

The application MUST work completely without Google Cloud.

SQLite is the authoritative application database and local source of truth.

Google Cloud is an additive layer for:
- analytics
- exports
- optional deployment
- cloud demonstration
- Data Agent Kit/MCP-assisted workflows

If Google Cloud is unavailable, misconfigured, or temporarily unreachable:
- the application must still start
- simulations must still run
- historical runs must still work
- reports must still be generated locally

Never make the core simulator dependent on a cloud service.

## 0.3 Explainable engineering

Prefer designs that are:
- deterministic when needed
- reproducible
- testable
- modular
- explainable
- backed by clear algorithms

Avoid "magic" abstractions that make the project difficult to explain.

---

# 1. GOOGLE CLOUD + BILLING POLICY

Read this section carefully before doing anything cloud-related.

## 1.1 Project

Use:

```text
Project ID: bcdrsimulator-sail
Primary region: us-central1
```

Use the already-authenticated Google Cloud environment and Application Default Credentials.

Never hard-code credentials.

Never put credentials, access tokens, OAuth tokens, or ADC files into source control.

---

## 1.2 ZERO OUT-OF-POCKET TARGET

The target is:

**₹0 / $0 out of pocket.**

This means:

- Do not intentionally create usage that exceeds applicable free limits.
- Do not intentionally generate large workloads.
- Do not create production-scale infrastructure.
- Do not request payment information.
- Do not upgrade the account just to make a feature work.

However:

**DO NOT interpret this as "avoid Google Cloud."**

You may use legitimate Google Cloud services normally when they materially improve the project and expected usage is small enough to remain comfortably within applicable Free Tier / Free Trial allowances.

Examples that may be used where appropriate:
- BigQuery
- Cloud Storage
- Cloud Run
- Cloud Functions
- Compute Engine
- Artifact Registry
- Cloud Monitoring / Logging where useful
- Data Agent Kit / MCP
- other suitable Google Cloud services

Use only the smallest reasonable configuration.

---

## 1.3 Never ask for payment

NEVER ask me to:
- add a credit/debit card
- add a payment method
- purchase credits
- approve a charge
- upgrade to a paid billing account
- subscribe to a paid service
- buy a paid API
- activate a paid-only feature

If Google Cloud explicitly responds that an operation requires a paid upgrade/subscription/payment:

**STOP THAT OPERATION.**

Do not ask me whether I want to pay.

Instead:
1. explain which operation required paid access
2. do not execute it
3. implement the closest free/local alternative
4. continue the project

---

## 1.4 Free Tier / Free Trial discipline

Treat Free Tier / Free Trial as a resource budget, not as an excuse to create unnecessary infrastructure.

Use:
- small synthetic datasets
- low request volumes
- short-lived development workloads
- minimal CPU/RAM
- small object sizes
- efficient queries
- limited data scans
- limited storage
- no production traffic

Avoid:
- large datasets
- high-frequency loops against cloud APIs
- expensive query scans
- GPU workloads
- high-memory compute
- always-on infrastructure
- large load tests
- unnecessary replicas
- unnecessary networking infrastructure

Where applicable, keep expected usage comfortably below the documented free allowance rather than deliberately approaching the limit.

---

## 1.5 Cost gate before cloud resource creation

Before creating any GCP resource, state internally and in the work log:

```text
Service:
Purpose:
Expected usage:
Applicable free program:
Expected cost:
Reason it is needed:
How it will be cleaned up:
```

If the resource is unnecessary, do not create it.

If it requires immediate paid access, do not create it.

If a local implementation is equally suitable, prefer the local implementation.

---

## 1.6 Budget safeguard

Create or verify a Billing → Budgets & Alerts budget of approximately $0–$1 as an additional monitoring safeguard, if the current billing configuration permits it without requesting a new paid account or payment method.

Remember:
- a budget is an alerting mechanism
- it is not a guaranteed hard spending cap
- it must not be treated as permission to exceed free limits

Never attempt to modify billing or payment settings automatically.

---

## 1.7 Cloud services to avoid by default

Do not add services simply to make the architecture look more complex.

Avoid these unless there is a compelling project requirement AND they are compatible with the cost policy:
- Pub/Sub
- Cloud SQL
- Dataflow
- GPU instances
- high-memory Compute Engine
- GKE
- Cloud NAT
- VPN
- load balancers
- premium networking
- paid AI APIs
- always-on production infrastructure

For this project, use local alternatives when practical:
- SQLite instead of Cloud SQL
- local queue/event queue instead of Pub/Sub
- local/discrete-event simulation instead of Dataflow
- deterministic/rule-based AI-like recommendations instead of a paid LLM API

---

## 1.8 Data Agent Kit / MCP

Use the installed Google Cloud Data Agent Kit and MCP capabilities where they provide real value.

Treat them as development/data tooling, not as a replacement for the simulator's core logic.

Possible uses:
- BigQuery exploration
- Cloud Storage operations
- data analytics
- notebook generation
- visualization workflows
- natural-language exploration of historical simulation data

Do NOT make the core simulator's correctness depend on an LLM.

If an AI feature can be implemented deterministically, do that first.

If a natural-language feature is genuinely useful, Data Agent Kit/MCP may be used as an optional layer.

Never put an access token into MCP configuration manually.

Use existing authentication / ADC.

---

# 2. PROJECT ARCHITECTURE

Use this logical architecture:

```text
                         USER
                          |
                          v
                    STREAMLIT APP
                          |
             +------------+------------+
             |                         |
             v                         v
       LOCAL SIMULATION          GOOGLE CLOUD
             |                    (optional)
       +-----+------+          +---+---+------+
       |     |      |          |       |      |
       v     v      v          v       v      v
    SQLite NetworkX Plotly  BigQuery Storage Cloud Run
      |                          |
      +--------------------------+
                 Analytics / Export
```

Hard requirement:

**SQLite is the source of truth.**

Google Cloud is additive only.

---

# 3. TECHNOLOGY STACK

## Core

Use:
- Python 3.x
- Streamlit
- NetworkX
- SQLite
- Pandas
- NumPy
- Plotly
- Pydantic
- pytest

Recommended additions where justified:
- Hypothesis for property-based tests
- jsonschema for scenario validation

## Cloud

Optional:
- BigQuery
- Cloud Storage
- Cloud Run
- Artifact Registry
- Data Agent Kit / MCP

Do not add a service unless it has a clear architectural purpose.

---

# 4. PROJECT PURPOSE

Build an interactive BC/DR simulation platform that models:

- business services
- IT systems
- infrastructure
- dependencies
- disasters
- failure propagation
- uncertainty
- decision-making
- recovery strategies
- business impact
- RTO/RPO
- risk
- resilience
- historical replay
- counterfactual recovery decisions

The application should feel like a serious tabletop/decision-support simulator rather than a simple graph demo.

---

# 5. INDUSTRY-GROUNDED BC/DR TERMINOLOGY

Use standard terminology from established BC/DR practice where appropriate, rather than inventing game-like terms.

Include:

## BIA — Business Impact Analysis

Before a crisis simulation begins, allow the user to score business services by criticality, including a 1–10 impact/criticality scale.

The BIA score must influence:
- resilience scoring
- prioritization
- recovery decisions
- business impact

## RTO — Recovery Time Objective

The target time to restore a service.

## RPO — Recovery Point Objective

The acceptable amount of data loss measured in time.

## MTPD — Maximum Tolerable Period of Disruption

The absolute maximum period the business can tolerate before a service disruption becomes unacceptable.

RTO and MTPD must be distinct.

Crossing MTPD should produce a special business-failure state rather than merely lowering a score.

## WRT — Work Recovery Time

Technical recovery is not necessarily the same as business recovery.

A system can be restored while business backlog remains.

Model this separately where useful.

## RCO — Recovery Consistency Objective

For replicated/distributed systems, optionally model the expected consistency state after failover.

Keep this feature simple and explainable.

---

# 6. FUNCTIONAL FEATURES

The application must support:

1. Organization setup
2. Business service setup
3. System/infrastructure modeling
4. Dependency graph creation
5. Criticality assignment
6. BIA
7. RTO definition
8. RPO definition
9. MTPD definition
10. WRT tracking
11. Disaster scenario selection
12. Failure propagation
13. Partial degradation
14. Investigation under uncertainty
15. Recovery decisions
16. Resource constraints
17. Recovery strategy comparison
18. Risk calculation
19. Single-point-of-failure detection
20. Historical run storage
21. Replay
22. Counterfactual replay
23. Monte Carlo mode
24. Cloud analytics/export
25. Report generation

Do not add unrelated platform features.

---

# 7. DISASTER SCENARIOS

Provide realistic simulation-only scenarios:

- server failure
- database failure
- network outage
- data-center outage
- cloud-region outage
- power failure
- ransomware incident
- data corruption
- cyberattack
- cloud service outage
- supply-chain disruption

These are simulations.

Do NOT implement:
- malware
- exploit delivery
- credential theft
- real ransomware
- offensive intrusion
- destructive cloud actions

---

# 8. DEPENDENCY GRAPH MODEL

Represent systems/services as a directed graph.

Example:

```text
Internet
   |
   v
Firewall
   |
   v
Application Server
   |
   v
Database
   |
   v
Payment Service
```

Dependencies must support:

```text
hard
soft
```

A hard dependency means service operation strongly depends on the upstream dependency.

A soft dependency means service can degrade without it.

Dependencies should also have a weight, for example:

```text
weight = 1.0
weight = 0.3
```

Use weighted propagation rather than pure binary failure.

---

# 9. PARTIAL-CAPACITY PROPAGATION

Do not model everything as simply:

```text
UP
DOWN
```

Model health/availability on a scale such as:

```text
0.0 -> fully unavailable
1.0 -> fully healthy
```

A system's effective availability should depend on:
- its own health
- health of upstream dependencies
- dependency type
- dependency weight

Example conceptual formula:

```python
effective_availability =
    own_health * dependency_factor
```

Use an explainable implementation.

---

# 10. SINGLE POINT OF FAILURE DETECTION

Use NetworkX to automatically identify infrastructure weaknesses before the crisis starts.

Include:
- degree centrality
- betweenness centrality
- PageRank where meaningful
- connected components
- shortest paths
- articulation points
- minimum vertex cuts where appropriate

Use articulation points / graph cuts to identify likely single points of failure.

Display a plain-English explanation:

Example:

> "Database A is a single point of failure because two critical business services have no alternate path if it becomes unavailable."

Do not display raw metrics without interpretation.

---

# 11. SIMULATION ENGINE — DISCRETE EVENT SIMULATION

Use a discrete-event simulation architecture rather than a naive fixed time-step loop.

Conceptually:

```text
Event Queue
    |
    v
Pop next event
    |
    v
Apply event
    |
    +--> update state
    |
    +--> schedule follow-up events
    |
    v
Repeat
```

The event queue may use `heapq` or an equivalent efficient priority queue.

Events may include:
- failure
- degradation
- propagation
- investigation completion
- recovery start
- recovery completion
- decision deadline
- communication deadline
- data restore completion
- business backlog recovery

---

# 12. SEEDED RANDOMNESS + UNCERTAINTY

Every simulation run must have a stored RNG seed.

Store the seed in the SQLite `simulation_runs` table.

Recovery actions must not always take exactly one deterministic amount of time.

Represent an action with:

```text
optimistic time
likely time
pessimistic time
cost variance
```

Use a triangular or PERT-like distribution.

Conceptually:

```python
sampled_time = rng.triangular(
    optimistic,
    pessimistic,
    likely,
)
```

This creates realistic uncertainty while keeping every run reproducible.

---

# 13. HEADLESS SIMULATION ENGINE

The simulation engine must have zero Streamlit dependency.

Provide something equivalent to:

```python
run_headless(
    scenario,
    decisions,
    seed
) -> SimulationResult
```

This function must be usable from:
- pytest
- CLI scripts
- Monte Carlo runs
- replay tools
- counterfactual analysis

The engine should behave as a pure/reproducible function of its inputs and stored decision history, avoiding hidden mutable global state.

---

# 14. INCOMPLETE INFORMATION + INVESTIGATION

Add a genuine uncertainty mechanic.

Hidden facts may include:
- corruption percentage
- backup integrity
- true root cause
- actual dependency health
- recovery duration
- backup freshness

Represent:

```text
true value
known range
confidence
```

The user may spend time/resources investigating.

Investigation narrows the known range and raises confidence.

This must create an actual strategic trade-off:

```text
Investigate longer
    -> more information
    -> less uncertainty
    -> less time available for recovery
```

Do not make "Investigate" a cosmetic button.

---

# 15. RECOVERY STRATEGIES

Implement:

- backup restoration
- local backup restoration
- failover
- hot standby
- warm standby
- cold standby
- cloud recovery
- manual recovery
- service prioritization
- redundancy

Each strategy should have:
- optimistic time
- likely time
- pessimistic time
- resource requirement
- data-loss characteristics
- simulated recovery cost
- risk/benefit implications

The "cost" field is a business/recovery simulation variable.

Do not confuse simulated cost with actual Google Cloud billing.

---

# 16. RESOURCE CONSTRAINTS

The simulation should model finite resources such as:

- recovery team capacity
- infrastructure capacity
- backup availability
- maintenance windows
- recovery budget
- technician availability
- communication capacity

Decisions should have consequences.

Avoid making every recovery action simultaneously possible.

---

# 17. EXPLAINABLE SCORE SYSTEM

Use a resilience/risk score that is understandable.

Core risk model:

```text
Risk = Probability × Impact × Exposure
```

Risk categories:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Resilience score may contain categories such as:
- Recovery Performance
- Data Protection
- Business Availability
- Resource Efficiency
- Cost Efficiency

Every decision should generate a score event.

Each score event must contain:

```text
decision_id
category
delta
reason
timestamp
```

Example:

> "RTO worsened by 45 minutes because database restoration was delayed by an unavailable backup."

This creates an explainable score ledger rather than a black-box final number.

---

# 18. BUSINESS IMPACT MODEL

Add a thin but realistic business layer.

Support:
- revenue-loss rate
- SLA penalty clauses
- reputation decay
- regulatory notification clocks for relevant scenarios
- business backlog
- customer-impact indicators

Example:

```text
Payment Processing:
₹10,000 simulated penalty per hour after 1 hour
```

These are simulation values, not real billing.

For data-compromise scenarios, allow configurable notification deadlines.

Do not hard-code legal advice; model deadlines as scenario parameters.

---

# 19. RECOVERY REPORT

At the end of a run, produce a detailed report including:

## Incident summary
- scenario
- start time
- affected systems
- severity

## BIA
- business service criticality
- tolerable downtime
- impact ranking

## Recovery
- decisions
- recovery sequence
- actual recovery times
- resource usage

## RTO/RPO
- target
- actual
- pass/fail

## MTPD
- whether the disruption crossed MTPD

## WRT
- technical recovery vs business recovery

## Risk
- risk score
- major risks
- single points of failure

## Score ledger
- positive and negative decision deltas

## Recommendations
- backup changes
- redundancy
- dependency improvements
- recovery strategy improvements

---

# 20. COUNTERFACTUAL REPLAY

Add a feature after the core MVP is stable:

User selects a previous decision point.

The simulator should:
1. use the same original seed
2. replay the same events up to the chosen decision
3. branch from that point
4. use an alternative decision
5. compare outcomes

Show:

```text
Original:
Restore from local backup
RTO: 3.5h
Resilience: 62

Counterfactual:
Activate warm standby
RTO: 1.2h
Resilience: 84
```

This is one of the most valuable advanced features in the project.

---

# 21. MONTE CARLO MODE

Use the seeded simulation architecture to support repeated runs.

Allow the user to run the same strategy configuration many times with different seeds.

Display distributions such as:
- resilience score
- RTO
- downtime
- simulated cost
- probability of MTPD breach

Use:
- histogram
- box plot
- percentile metrics

Explain that resilience is about tail risk, not only average performance.

Use modest run counts by default, e.g. 100–200.

Do not use huge compute workloads.

---

# 22. STRATEGY COMPARISON

Compare recovery strategies using:
- RTO
- RPO
- downtime
- simulated cost
- resilience
- risk
- resource use

Use:
- table
- small-multiple charts
- clear recommendation
- explainability

Do not declare a "best" strategy purely from a single numeric score.

Show trade-offs.

---

# 23. VISUALIZATIONS

Use Plotly extensively.

Required visualizations:

## Dependency graph
Interactive NetworkX-derived graph.

## Failure propagation
Show the cascade.

## Recovery timeline
Show:
- failure
- investigation
- recovery actions
- service recovery
- business recovery

## Risk heatmap

## Strategy comparison

## Resilience radar
Suggested five dimensions:
- Recovery Performance
- Data Protection
- Business Availability
- Resource Efficiency
- Cost Efficiency

## Score timeline
Show score changes over time and annotate major decisions.

## Sankey diagram
Show:

```text
Failure source
    ->
Affected systems
    ->
Business services
    ->
Business impact
```

The Sankey diagram should visually explain how a technical failure becomes a business-impact event.

---

# 24. STREAMLIT UI

Build a polished professional dashboard.

Navigation:

```text
Dashboard
Organization
Business Impact Analysis
Infrastructure
Dependency Graph
Disaster Scenarios
Simulation
Investigation
Recovery Planning
Risk Analysis
Strategy Comparison
Historical Runs
Replay / Counterfactuals
Monte Carlo
Google Cloud
Settings
```

## Dashboard

Show:
- overall resilience
- active scenario
- affected systems
- RTO status
- RPO status
- MTPD status
- risk category
- critical dependencies
- top recommendations

## Organization

Allow:
- business services
- system inventory
- criticality
- RTO
- RPO
- MTPD
- SLA parameters

## BIA

Allow users to rank services.

## Infrastructure

Allow users to create:
- systems
- resources
- dependencies
- dependency types
- dependency weights

## Scenario builder

Allow selection and customization of scenarios.

## Simulation

Show:
- timeline
- current state
- actions
- resource constraints
- score changes

## Investigation

Show confidence ranges and allow investigation actions.

## Recovery

Show strategy choices and consequences.

## Historical Runs

Provide:
- table
- filters
- load/replay
- export

---

# 25. SQLITE DATABASE

Use SQLite.

Required conceptual tables:

```text
organizations
systems
business_services
dependencies
scenarios
simulation_runs
failure_events
recovery_events
recovery_strategies
risk_assessments
simulation_results
score_events
hidden_facts
```

Recommended additions where useful:

```text
decisions
bia_assessments
sla_rules
notification_deadlines
cloud_exports
```

Important fields:

`simulation_runs`
- id
- scenario
- start_time
- end_time
- rng_seed
- team_id (optional future-ready field)

`dependencies`
- source
- target
- dep_type
- weight

`score_events`
- id
- run_id
- decision_id
- category
- delta
- reason

`hidden_facts`
- id
- run_id
- fact_key
- true_value
- revealed_low
- revealed_high
- confidence
- updated_at

Database initializes automatically.

SQLite remains authoritative.

---

# 26. SCENARIO VALIDATION

Scenario definitions should be JSON files where practical.

Use a JSON Schema.

Validate:
- required fields
- data types
- allowed enums
- ranges
- dependencies
- recoveries
- actions

Return human-readable validation errors.

An invalid instructor-authored scenario must not crash the simulator midway through execution.

---

# 27. GOOGLE CLOUD INTEGRATION

Google Cloud integration is optional but should be real.

## BigQuery

Use for analytics such as:
- historical run analysis
- risk trends
- recovery metrics
- strategy comparisons

Mirror only analytics-relevant data, such as:
- simulation_runs
- risk_scores / risk assessments
- recovery_metrics

Use small synthetic datasets.

Use narrow queries.

Prefer filters and `LIMIT`.

Never scan large datasets unnecessarily.

If BigQuery is unavailable:
- use SQLite/Pandas
- show a friendly status in the UI

## Cloud Storage

Use for small:
- CSV exports
- JSON exports
- reports
- scenario files
- simulation snapshots

Do not upload unnecessary files.

## Cloud Run

Cloud Run deployment is optional after local validation.

Use:
- minimal resources
- low traffic
- no unnecessary minimum instances
- small container image

Do not automatically deploy to production.

If deployment requires a paid upgrade:
- stop
- do not ask to pay
- keep local deployment

## Artifact Registry

Use only if required by Cloud Run container deployment.

Keep images small.

Clean up obsolete images when safe.

---

# 28. GOOGLE CLOUD PANEL IN THE APP

Include a Google Cloud page that can show:

```text
Authentication status
Project ID
Region
BigQuery availability
Cloud Storage availability
Cloud Run/deployment status
Data Agent Kit/MCP availability
```

Make cloud failures non-fatal.

Do not reveal credentials or access tokens in the UI.

---

# 29. SECURITY

Strictly:
- no secrets in repository
- no tokens in source code
- no credentials in README
- no real personal data
- no private client data
- synthetic data only

Use:
- `.env`
- `.env.example`
- `.gitignore`
- ADC

Never commit:
- ADC JSON
- credential files
- API keys
- OAuth tokens
- private keys

The account email should not be hard-coded into application logic.

---

# 30. CLOUD RESOURCE CLEANUP

When creating temporary cloud resources:
- clean up unused datasets
- remove unnecessary Cloud Storage objects
- clean unused container images
- stop/delete temporary VMs
- avoid leaving test services running

Do not delete resources without checking whether the resource is part of the active project.

Never perform destructive cleanup against unrelated projects.

---

# 31. OPTIONAL PHASE 2 FEATURES

After the single-user MVP is stable and demoable, optionally implement:

## Role-based tabletop simulation

Roles:
- Incident Commander
- IT Manager
- Security Analyst
- Business Manager

Different roles can see different slices of information.

Use Streamlit session state / room codes.

No real-time infrastructure is required for the prototype.

Do NOT put multiplayer ahead of the core simulator.

## Instructor analytics

Optional later:
- cohort comparison
- box plots across runs
- sortable score table
- CSV export for grading
- live instructor event injection

These are Phase 2/3 features, not MVP requirements.

---

# 32. TESTING

Use pytest.

Test:
- graph construction
- dependency propagation
- partial degradation
- articulation-point detection
- risk calculations
- RTO/RPO calculations
- MTPD handling
- WRT calculations
- score ledger
- deterministic seed replay
- counterfactual replay
- database persistence
- scenario validation

Use property-based testing with Hypothesis where appropriate.

Example invariants:

```text
budget never becomes negative
health remains within valid bounds
risk score remains within documented range
simulation replay with the same seed produces equivalent outcomes
invalid scenario definitions are rejected
```

---

# 33. CI/CD

Create:

```text
.github/workflows/test.yml
```

Run:
- pytest
- Hypothesis tests
- basic lint/type checks where practical

Do not add CI cloud deployment automatically.

The initial CI requirement is simply:

**build/test reliability.**

---

# 34. PROJECT DIRECTORY

Use a structure similar to:

```text
bcdr-simulator/
|
+-- app/
|   +-- main.py
|
|   +-- core/
|       +-- simulation_engine.py
|       +-- event_queue.py
|       +-- failure_propagation.py
|       +-- recovery_engine.py
|       +-- risk_engine.py
|       +-- scoring.py
|
|   +-- models/
|       +-- organization.py
|       +-- system.py
|       +-- business_service.py
|       +-- dependency.py
|       +-- disaster.py
|       +-- recovery_plan.py
|       +-- simulation.py
|
|   +-- graph/
|       +-- dependency_graph.py
|       +-- graph_analysis.py
|
|   +-- database/
|       +-- sqlite_manager.py
|       +-- repositories.py
|       +-- schema.sql
|
|   +-- cloud/
|       +-- gcp_client.py
|       +-- bigquery_client.py
|       +-- storage_client.py
|
|   +-- visualization/
|       +-- dependency_graph.py
|       +-- recovery_timeline.py
|       +-- risk_charts.py
|       +-- sankey.py
|       +-- strategy_comparison.py
|
|   +-- ui/
|       +-- dashboard.py
|       +-- organization.py
|       +-- bia.py
|       +-- infrastructure.py
|       +-- scenarios.py
|       +-- simulation.py
|       +-- investigation.py
|       +-- recovery.py
|       +-- risk.py
|       +-- historical.py
|       +-- cloud.py
|
+-- scenarios/
+-- data/
+-- tests/
+-- scripts/
+-- docs/
+-- .github/
+-- requirements.txt
+-- README.md
+-- .env.example
+-- .gitignore
```

You may improve this structure where appropriate.

---

# 35. DEVELOPMENT ORDER

Follow this sequence.

## Phase 0 — Inspect

1. Inspect workspace.
2. Inspect existing files.
3. Inspect dependencies.
4. Inspect current GCP configuration.
5. Inspect Data Agent Kit/MCP availability.

Do not destroy or overwrite useful existing work.

## Phase 1 — Architecture

Define:
- application architecture
- database schema
- simulation state model
- event model
- dependency model
- recovery model

## Phase 1.5 — Engineering foundations

Before UI polish:
- discrete-event event queue
- seeded RNG
- headless engine
- initial test suite

## Phase 2 — MVP

Implement:
- systems
- business services
- dependencies
- basic scenarios
- binary + initial partial propagation
- core decisions
- recovery
- RTO/RPO
- risk
- Streamlit
- SQLite

## Phase 2.5 — Realism

Add:
- weighted propagation
- articulation-point SPOF detection
- investigation/uncertainty
- MTPD
- WRT
- score ledger

## Phase 3 — Advanced analytics

Add:
- counterfactual replay
- Monte Carlo
- strategy comparison
- Sankey
- radar
- small multiples
- scenario validation
- property-based tests
- CI

## Phase 4 — Cloud integration

After local functionality is stable:
- BigQuery analytics
- Cloud Storage exports
- optional Cloud Run deployment
- Google Cloud dashboard
- MCP-assisted analytics

Cloud integration must never break local operation.

## Phase 5 — Optional Phase 2/3 extras

Only if the core project is already excellent:
- role-based tabletop sessions
- instructor/cohort analytics
- live event injection

---

# 36. DOCUMENTATION

Create:

```text
README.md

docs/
+-- architecture.md
+-- simulation-model.md
+-- database-schema.md
+-- gcp-integration.md
+-- security.md
+-- development.md
```

README must explain:
- project purpose
- architecture
- setup
- local execution
- database
- simulation model
- BC/DR concepts
- BIA
- RTO/RPO
- MTPD
- WRT
- risk
- NetworkX analysis
- GCP integration
- Data Agent Kit/MCP
- Free Tier vs Free Trial considerations
- security
- testing
- future work

The documentation must be written so I can use it to explain the project in an interview.

---

# 37. DEMONSTRATION SCENARIO

Create at least one polished default demonstration scenario.

Example:

```text
Organization:
FinServe Demo

Business Services:
- Payment Processing
- Customer Portal
- Internal Reporting

Systems:
- Internet Gateway
- Firewall
- Application Cluster
- Primary Database
- Read Replica
- Cache
- Backup System

Scenario:
Primary Database Failure
```

The demo should visibly show:
1. failure
2. propagation
3. investigation
4. recovery decision
5. service restoration
6. business recovery
7. RTO/RPO results
8. risk impact
9. score changes
10. recommendations

Use synthetic data only.

---

# 38. QUALITY STANDARD

The result must NOT feel like:
- a beginner Streamlit tutorial
- a static dashboard
- a graph visualization with buttons
- a fake cloud architecture diagram
- a black-box scoring game

It should feel like a legitimate engineering/simulation portfolio project.

Prioritize:
- real simulation logic
- reproducibility
- explainability
- testability
- meaningful graph algorithms
- realistic business impact
- clean data modeling
- sensible cloud integration

---

# 39. ANTI-OVERENGINEERING RULE

Do not add:
- unnecessary microservices
- unnecessary APIs
- unnecessary Kubernetes
- unnecessary distributed systems
- unnecessary authentication platforms
- unnecessary event buses
- unnecessary external databases

Every component must have a reason.

The question for every architectural choice is:

> "Does this materially improve the simulator or teach an important engineering concept?"

If not, do not add it.

---

# 40. FINAL OPERATING HIERARCHY

Always follow:

```text
1. SECURITY
   |
   v
2. NO PAYMENT REQUESTS / NO PAID UPGRADE
   |
   v
3. LOCAL FUNCTIONALITY MUST REMAIN INTACT
   |
   v
4. USE FREE GOOGLE CLOUD SERVICES NORMALLY WHEN THEY ADD REAL VALUE
   |
   v
5. KEEP CLOUD WORKLOADS SMALL AND COMFORTABLY WITHIN FREE LIMITS
   |
   v
6. BUILD A TECHNICALLY DEFENSIBLE SIMULATOR
   |
   v
7. KEEP EVERYTHING EXPLAINABLE IN AN INTERVIEW
```

---

# 41. FIRST RESPONSE REQUIRED FROM YOU, THE AGENT

Before writing implementation code:

### A. Inspect the current workspace.

### B. Report:
1. current file structure
2. existing dependencies
3. current Python environment
4. existing Streamlit setup
5. existing GCP configuration
6. Data Agent Kit/MCP status
7. detected gaps

### C. Produce:
1. architecture diagram
2. component responsibilities
3. SQLite schema
4. simulation state model
5. event model
6. dependency propagation model
7. recovery model
8. risk model
9. GCP integration plan
10. cloud-cost/free-tier strategy
11. development roadmap

### D. Do NOT:
- create paid resources
- upgrade billing
- ask for payment
- deploy to production
- create large cloud workloads
- immediately generate dozens of files without first showing the plan

### E. Start with local implementation.

Once the architecture is established, begin implementation incrementally.

After each major milestone:
- run tests
- validate the application
- summarize what changed
- explain why it was chosen
- identify any risks or trade-offs

The final result should be a complete, working, documented, testable Adaptive Business Continuity & Disaster Recovery Simulator with meaningful optional Google Cloud integration and strict control over cost, credentials, and operational risk.
