import streamlit as st
from app.core.simulation_engine import SimulationEngine
import app.ui.state_manager as state_manager
from app.visualization import charts
from app.models.enums import SimulationStatus

def render():
    st.header("Simulation Engine Control")
    
    if "engine" not in st.session_state:
        st.warning("Engine not initialized.")
        return
        
    engine: SimulationEngine = st.session_state["engine"]
    scenario = st.session_state.get("active_scenario")
    
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.metric("Simulation Time", f"{engine.current_time:.2f} hours")
    with col2:
        with st.container(border=True):
            st.metric("Events in Queue", len(engine.events))
        
    st.markdown("---")
    
    # Engine Controls
    st.subheader("Controls")
    with st.container(border=True):
        ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns(4)
        
        with ctrl_col1:
            if st.button("Trigger Disaster", disabled=engine.current_time > 0):
                impacts = {a.system_id: a.health_impact for a in scenario.affected_systems}
                engine.trigger_disaster(impacts)
                st.success("Disaster triggered!")
                st.rerun()
                
        with ctrl_col2:
            if st.button("Step Event", disabled=engine.events.is_empty()):
                evt = engine.step()
                st.toast(f"Executed: {evt.event_type.name} at T={evt.time:.2f}")
                st.rerun()
                
        with ctrl_col3:
            if st.button("Run Until Empty", disabled=engine.events.is_empty()):
                engine.run_until_empty()
                st.rerun()
                
        with ctrl_col4:
            is_completed = engine.run_data.status == SimulationStatus.COMPLETED
            if st.button("Save Run", disabled=not is_completed, type="primary"):
                try:
                    state_manager.save_current_run(engine)
                    st.success("Run saved successfully!")
                except Exception as e:
                    st.error(f"Failed to save run: {str(e)}")



    st.markdown("---")
    
    st.subheader("Simulation Timeline")
    with st.container(border=True):
        fig_gantt = charts.generate_timeline_gantt(engine)
        st.plotly_chart(fig_gantt, use_container_width=True, key=f"timeline_chart_{len(engine.processed_events)}")

    st.markdown("---")
    
    # Event Timeline / Ledger
    st.subheader("Simulation Ledger (Score & Events)")
    with st.container(border=True):
        ledger = engine.scoring.get_ledger()
        if not ledger:
            st.info("No business impacts logged yet. Score ledger is empty.")
        else:
            log_data = []
            for l in ledger:
                log_data.append({
                    "Time (h)": f"{l.event_time:.2f}",
                    "Category": l.category.value,
                    "Delta": f"{l.delta:+.1f}",
                    "Description": l.reason
                })
            
            import pandas as pd
            df_log = pd.DataFrame(log_data)
            def color_delta(val):
                try:
                    if float(val) < 0:
                        return 'color: #f43f5e; font-weight: bold;'
                    elif float(val) > 0:
                        return 'color: #10b981; font-weight: bold;'
                except:
                    pass
                return ''
            st.dataframe(df_log.style.map(color_delta, subset=['Delta']), use_container_width=True)

    st.markdown("---")
    
    st.subheader("Processed Event Ledger")
    with st.container(border=True):
        if not engine.processed_events:
            st.info("No events have been processed yet.")
        else:
            event_data = []
            for e in engine.processed_events:
                event_data.append({
                    "Time (h)": f"{e.time:.2f}",
                    "System": e.system_id,
                    "Event": e.event_type.name,
                    "Description": e.description
                })
            df_ev = pd.DataFrame(event_data)
            st.dataframe(df_ev, use_container_width=True)

    # Detailed State
    st.subheader("Current State Snapshots")
    with st.container(border=True):
        tab1, tab2 = st.tabs(["System States", "Service Impacts"])
        
        with tab1:
            sys_data = []
            for sys_id, state in engine.system_states.items():
                is_recovering = engine.recovery.is_system_recovering(sys_id)
                avail = state.effective_availability * 100
                
                if is_recovering:
                    status = "Recovering 🔄"
                elif avail >= 100:
                    status = "Healthy 🟢"
                elif avail <= 0:
                    status = "Failed 🔴"
                else:
                    status = "Degraded 🟡"
    
                sys_data.append({
                    "System": sys_id,
                    "Availability": f"{avail:.0f}%",
                    "Status": status
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
                st.info("No business impacts recorded yet.")
