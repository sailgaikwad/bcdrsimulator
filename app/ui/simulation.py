import streamlit as st
from app.core.simulation_engine import SimulationEngine
import app.ui.state_manager as state_manager
from app.visualization import charts

def render():
    st.header("Simulation Engine Control")
    
    if "engine" not in st.session_state:
        st.warning("Engine not initialized.")
        return
        
    engine: SimulationEngine = st.session_state["engine"]
    scenario = st.session_state.get("active_scenario")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Simulation Time", f"{engine.current_time:.2f} hours")
    with col2:
        st.metric("Events in Queue", len(engine.events))
        
    st.markdown("---")
    
    # Engine Controls
    st.subheader("Controls")
    
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns(4)
    
    with ctrl_col1:
        if st.button("🚨 Trigger Disaster", disabled=engine.current_time > 0):
            # Apply the initial impact from the scenario
            impacts = {a.system_id: a.health_impact for a in scenario.affected_systems}
            engine.trigger_disaster(impacts)
            st.success("Disaster triggered! Failure propagated across dependencies.")
            st.rerun()
            
    with ctrl_col2:
        if st.button("⏭️ Step Event", disabled=engine.events.is_empty()):
            evt = engine.step()
            st.toast(f"Executed: {evt.event_type.name} at T={evt.time:.2f}")
            st.rerun()
            
    with ctrl_col3:
        if st.button("⏩ Run Until Empty", disabled=engine.events.is_empty()):
            engine.run_until_empty()
            st.rerun()
            
    with ctrl_col4:
        is_completed = engine.current_time > 0 and engine.events.is_empty()
        if st.button("💾 Save Run", disabled=not is_completed, type="primary"):
            try:
                state_manager.save_current_run(engine)
                st.success("Run saved successfully! View it in 'Historical Runs'.")
            except Exception as e:
                st.error(f"Failed to save run: {str(e)}")

    if st.button("🔄 Reset Simulation"):
        state_manager.reset_simulation()
        st.rerun()

    st.markdown("---")
    
    st.subheader("Simulation Timeline")
    fig_gantt = charts.generate_timeline_gantt(engine)
    st.plotly_chart(fig_gantt, use_container_width=True, key="timeline_chart")

    st.markdown("---")
    
    # Event Timeline / Ledger
    st.subheader("Simulation Ledger (Score & Events)")
    
    ledger = engine.scoring.get_ledger()
    if not ledger:
        st.info("No events logged yet. Trigger the disaster to begin.")
    else:
        log_data = []
        for l in ledger:
            log_data.append({
                "Time (h)": f"{l.event_time:.2f}",
                "Category": l.category.value,
                "Delta": f"{l.delta:+.1f}",
                "Description": l.reason
            })
        st.dataframe(log_data, use_container_width=True)

    # Detailed State
    st.subheader("Current State Snapshots")
    tab1, tab2 = st.tabs(["System States", "Service Impacts"])
    
    with tab1:
        sys_data = []
        for sys_id, state in engine.system_states.items():
            sys_data.append({
                "System": sys_id,
                "Availability": f"{state.effective_availability*100:.0f}%"
            })
        st.dataframe(sys_data, use_container_width=True)
        
    with tab2:
        svc_data = []
        for svc in engine.services:
            impact = engine.bia.get_impact(svc.id)
            if impact:
                svc_data.append({
                    "Service": svc.name,
                    "Downtime": f"{impact.downtime_hours:.2f}h",
                    "Revenue Lost": f"INR {impact.revenue_lost:,.2f}",
                    "MTPD Breached": impact.mtpd_breached
                })
        if svc_data:
            st.dataframe(svc_data, use_container_width=True)
        else:
            st.write("No business impacts recorded yet.")
