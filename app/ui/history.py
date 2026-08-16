import streamlit as st
import json
import pandas as pd
from app.database.sqlite_manager import SQLiteManager
from app.database.repositories import SimulationRunRepository

def render():
    st.header("Historical Runs")
    st.markdown("<p style='color: var(--text-muted);'>Review completed simulations, including final state and full event ledgers.</p>", unsafe_allow_html=True)
    
    if "db" not in st.session_state:
        st.warning("Database not initialized.")
        return
        
    db: SQLiteManager = st.session_state["db"]
    run_repo = SimulationRunRepository(db)
    org_id = "org-finserve"
    
    runs = run_repo.list_by_org(org_id)
    if not runs:
        st.info("No historical runs found. Run a simulation and click 'Save Run' in the Simulation tab.")
        return
        
    with st.container(border=True):
        st.markdown("Select a historical run to view its final state and score ledger.")
    
    # Format runs for selection
    run_options = {
        f"Run {r.id[:8]} ({r.status.value.upper()}) - Score: {r.final_resilience_score}": r
        for r in runs
    }
    
    selected_name = st.selectbox("Select Run", list(run_options.keys()))
    selected_run = run_options[selected_name]
    
    st.markdown("---")
    
    with st.container(border=True):
        st.subheader(f"Run Details: {selected_run.id}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Final Resilience Score", f"{selected_run.final_resilience_score:.1f}" if selected_run.final_resilience_score else "N/A")
        col2.metric("Total Downtime", f"{selected_run.total_downtime_hours:.2f}h" if selected_run.total_downtime_hours else "N/A")
        col3.metric("Final Status", selected_run.status.value.upper())
    
    with st.container(border=True):
        tab1, tab2 = st.tabs(["Event Ledger", "Final Service Impacts"])
    
    with tab1:
        if selected_run.event_ledger_json:
            ledger = json.loads(selected_run.event_ledger_json)
            if ledger:
                df = pd.DataFrame(ledger)
                st.dataframe(df, use_container_width=True)
            else:
                st.write("No events recorded.")
        else:
            st.write("Ledger data not available for this run.")
            
    with tab2:
        if selected_run.state_snapshot_json:
            snapshot = json.loads(selected_run.state_snapshot_json)
            services = snapshot.get("services", [])
            if services:
                df = pd.DataFrame(services)
                # Format currency
                df["revenue_lost"] = df["revenue_lost"].apply(lambda x: f"INR {x:,.2f}")
                st.dataframe(df, use_container_width=True)
            else:
                st.write("No service impact data available.")
        else:
            st.write("Snapshot data not available for this run.")
