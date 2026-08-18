# BCDR Simulator (Local + Google Cloud Enhanced)

This project focuses on building an adaptive simulation platform for business continuity and disaster recovery (BC/DR) training. While most organizations have continuity plans in place, these are often static documents that are rarely tested in realistic conditions. The aim of this project is to develop an instructor-led, interactive education tool that allows users to design and test continuity strategies in a practical and engaging way. 

The project focuses on how planning decisions—such as backup strategies, redundancy, and resource allocation—influence outcomes during a crisis. A key part of the work is developing a simulation engine that connects these decisions to measurable impacts, including recovery time, data loss, and overall business disruption. This allows users to move beyond theoretical planning and evaluate how their choices perform under pressure. 

The platform simulates events such as cyberattacks, system failures, and infrastructure outages, and shows how these can spread across interconnected systems. Users are required to make decisions under realistic constraints, including limited time, budget, and incomplete information. The simulation evolves over time, introducing new challenges and forcing users to adapt their plans as conditions change. In addition, the tool supports structured teaching scenarios, allowing instructors to guide sessions, introduce new events, and compare outcomes across different strategies. This creates opportunities for discussion, reflection, and iterative improvement, which are often missing from traditional BC/DR training approaches. The expected outcome is a working prototype that can be used as an instructor-led education tool to support more practical, experience-based learning in business continuity and organizational resilience. The project is relevant to both academic and industry settings, particularly in sectors where maintaining operations is critical.

## 🛠 Tech Stack
- **Frontend / UI:** Streamlit, Python
- **Simulation Engine:** Custom discrete-event engine (Python)
- **Persistence (Local):** SQLite (for ephemeral state and graceful offline capability)
- **Persistence (Cloud):** Google Cloud Storage (GCS) via Streamlit Secrets
- **Analytics:** Google BigQuery (Zero-Compute External Tables on GCS)
- **Containerization:** Docker

## 🏗 Architecture Overview

The system employs a hybrid architecture, operating locally for fast, deterministic simulation while being enhanced by Google Cloud for durable storage and analytics.

```mermaid
flowchart TD
    subgraph UI["Presentation Layer"]
        Streamlit["Streamlit UI (Cloud Run / Local)"]
    end
    
    subgraph App["Application Layer"]
        Engine["Discrete-Event Simulation Engine"]
        Engine -->|"Determinism"| RNG["RNG & Seed Management"]
        Engine -->|"Impact Assessment"| BIA["BIA Engine"]
    end

    subgraph Data["Persistence & Analytics (Hybrid)"]
        SQLite[("Local SQLite (bcdr.db)<br>Ephemeral State / Graceful Fallback")]
        GCS["Cloud Storage (GCS)<br>Durable Archival"]
        BQ[("BigQuery External Table<br>Zero-Compute Analytics")]
    end

    Streamlit <--> Engine
    Engine -->|"1. Save (Synchronous)"| SQLite
    Engine -->|"2. Export (Non-Blocking)"| GCS
    GCS -.->|"External Data Definition"| BQ
```

### Architectural Principles
- **Deterministic Simulation**: All events, scoring, and resolutions are reproducible using discrete RNG seeding.
- **Hybrid Persistence**: Run data is saved locally to SQLite first, then exported to Google Cloud Storage (GCS). This ensures that the application never crashes if network or GCP credentials fail (Graceful Offline Degradation).
- **Serverless Analytics**: We use a **BigQuery External Table** directly mapped to the GCS export bucket. This provides immediate, schema-enforced analytical queryability over historical simulation runs without requiring active ingestion pipelines.
- **Secure Cloud Run Deployment**: The application is deployed in a stateless Cloud Run container using Single Concurrency (`--concurrency=1`) to eliminate write collisions on the ephemeral SQLite database. The deployment maintains least-privilege IAM isolation.

---

## 🚀 Setup & Execution

### Option 1: Local Python Execution

Ensure you are using Python 3.14+ (the current workspace version).

1. Create a virtual environment and install dependencies:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. Run the application:
   ```powershell
   .venv\Scripts\python -m streamlit run app/main.py
   ```

### Option 2: Docker Execution

1. Build the image:
   ```powershell
   docker build -t bcdrsimulator:local .
   ```
2. Run the container:
   ```powershell
   docker run --rm -p 8501:8501 bcdrsimulator:local
   ```

### Option 3: Streamlit Community Cloud (Hosted)

Simply visit the live, hosted application without any local setup:
👉 **[https://bcrdsimulator.streamlit.app](https://bcrdsimulator.streamlit.app)**

---

## 📉 Demonstration Scenario

The application automatically seeds a `bcdr.db` with the FinServe Demo configuration on startup. Follow these steps to demonstrate the cascading failure and BCDR recovery workflow:

1. **Review Infrastructure**: Navigate to the **Dependency Graph** tab to observe the pre-configured FinServe architecture (Gateways -> Firewalls -> Apps -> DBs -> Replicas).
2. **Inject Fault**: Go to the **Simulation** tab and click **🚨 Trigger Disaster** to simulate a Primary Database Failure.
3. **Observe Propagation**: Note how the failure cascades to dependent systems (e.g., Payment Processing and Customer Portal).
4. **Analyze Business Impact**: View the **Dashboard** to see the Impact Flow Sankey diagram and the RTO/MTPD Bar charts reflecting the current outage.
5. **Execute Recovery**: In the **Simulation** tab, click **⏩ Run Until Empty** to step through the automatic recovery actions and scoring penalties.
6. **Persist Simulation**: Once the simulation completes, click **💾 Save Run**. This writes to local SQLite and transparently exports to GCS.
7. **Audit the Ledger**: Navigate to the **Historical Runs** tab to view the immutable ledger and final business outcome.
8. **Evaluate Strategies**: Navigate to the **Strategy Comparison** tab to analyze deterministic trade-offs between "Restore from Backup" vs "Failover to Replica".

---

## ✅ Testing & Reproducibility

The project maintains a rigorous, fully automated test suite comprising 76 unit and UI integration tests (`AppTest`).

```powershell
.venv\Scripts\python -m pytest tests/ -v
```

Tests cover core simulation logic, deterministic graph traversal, persistence, UI rendering, and GCP authentication/network failure mocks ensuring the graceful degradation architecture is structurally sound.
