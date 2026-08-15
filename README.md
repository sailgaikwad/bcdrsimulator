# BCDR Simulator

The BCDR Simulator is an interactive, discrete-event simulation platform for evaluating Business Continuity and Disaster Recovery (BCDR) strategies. It deterministically models how technical failures propagate through a dependency graph and assesses their impact on business services, RTO/RPO targets, and Maximum Tolerable Period of Disruption (MTPD).

## Core Architecture
- **Headless Engine**: A fully deterministic, discrete-event Simulation Engine (`app.core.simulation_engine`).
- **Data Layer**: SQLite handles persistence of runs, configurations, and the event ledger.
- **UI Layer**: Streamlit provides interactive dashboards, dependency visualization, timeline graphs, and a Strategy Comparison engine.

## Local Setup

Ensure you are using Python 3.14+ (the current workspace version).

1. Create a virtual environment and activate it:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

## Running the Application

Start the Streamlit application:
```powershell
.venv\Scripts\python -m streamlit run app/main.py
```
Open `http://localhost:8501` in your browser.

## FinServe Demonstration Scenario

The application will automatically seed a local `bcdr.db` with the FinServe Demo configuration on first startup.

### How to run the demo:
1. Navigate to the **Dependency Graph** tab to observe the pre-configured FinServe architecture (Gateways -> Firewalls -> Apps -> DBs -> Replicas).
2. Go to the **Simulation** tab and click **🚨 Trigger Disaster** to simulate a Primary Database Failure.
3. Observe how the failure propagates to dependent systems (e.g., Payment Processing and Customer Portal).
4. View the **Dashboard** to see the Impact Flow Sankey diagram and the RTO/MTPD Bar charts.
5. In the **Simulation** tab, click **⏩ Run Until Empty** to step through the automatic recovery actions and scoring penalties.
6. Once the simulation completes, click **💾 Save Run**.
7. Navigate to the **Historical Runs** tab to view the immutable ledger and business outcome of the saved run.
8. Navigate to the **Strategy Comparison** tab to analyze deterministic trade-offs between "Restore from Backup" vs "Failover to Replica".

## Testing

Run the test suite using pytest. The suite includes both the headless core engine tests and the Streamlit `AppTest` UI integration tests.

```powershell
.venv\Scripts\python -m pytest tests/ -v
```
