import streamlit as st
from app.core.simulation_engine import SimulationEngine
from app.models.enums import SimulationStatus
from app.visualization import charts

def render():
    st.header("Dashboard")
    
    if "engine" not in st.session_state:
        st.warning("Simulation engine not initialized.")
        return
        
    engine: SimulationEngine = st.session_state["engine"]
    scenario = st.session_state.get("active_scenario")
    
    col1, col2, col3 = st.columns(3)
    
    # Overview
    with col1:
        with st.container(border=True):
            st.subheader("Overview")
        st.write(f"**Organization:** {engine.run_data.org_id}")
        st.write(f"**Status:** {engine.run_data.status.value.upper()}")
        if scenario:
            st.write(f"**Active Scenario:** {scenario.name}")
            
    # Resilience & Severity
    with col2:
        with st.container(border=True):
            st.subheader("Metrics")
        score = engine.scoring.get_composite_score()
        st.metric("Resilience Score", f"{score:.1f}/100")
        if scenario:
            st.metric("Incident Severity", f"{scenario.severity * 100:.0f}%")
            
    # Business State
    with col3:
        with st.container(border=True):
            st.subheader("Business State")
            is_failed = engine.run_data.status == SimulationStatus.FAILED
            state_color = "var(--danger)" if is_failed else "var(--success)"
            state_text = "FAILED (MTPD Breached)" if is_failed else "OPERATIONAL"
            st.markdown(f"<div style='font-size: 1.5rem; font-weight: 700; color: {state_color}; margin-bottom: 1rem;'>{state_text}</div>", unsafe_allow_html=True)
            st.write(f"**Simulation Time:** {engine.current_time:.2f} hours")

    st.markdown("---")
    
    # Affected Services & Systems
    st.subheader("Service Impact (BIA)")
    
    services_data = []
    for svc in engine.services:
        impact = engine.bia.get_impact(svc.id)
        if impact:
            mtpd_status = "BREACHED" if impact.mtpd_breached else "OK"
            rto_status = "BREACHED" if impact.downtime_hours > svc.rto_hours else "OK"
            
            services_data.append({
                "Service": svc.name,
                "Criticality": svc.criticality,
                "Downtime": f"{impact.downtime_hours:.2f}h",
                "RTO Target": f"{svc.rto_hours}h",
                "RTO Status": rto_status,
                "MTPD Target": f"{svc.mtpd_hours}h",
                "MTPD Status": mtpd_status,
                "Revenue Lost": f"INR {impact.revenue_lost:,.2f}"
            })
            
    if services_data:
        import pandas as pd
        df = pd.DataFrame(services_data)
        
        def highlight_status(val):
            if val == "BREACHED":
                return "color: white; background-color: #f43f5e; font-weight: bold;"
            elif val == "OK":
                return "color: white; background-color: #10b981; font-weight: bold;"
            return ""
            
        styled_df = df.style.map(highlight_status, subset=["RTO Status", "MTPD Status"])
        
        with st.container(border=True):
            st.dataframe(styled_df, use_container_width=True)
        
        st.subheader("RTO & MTPD Visualization")
        with st.container(border=True):
            fig_rto = charts.generate_rto_comparison(engine)
            st.plotly_chart(fig_rto, use_container_width=True, key=f"rto_chart_{len(engine.processed_events)}")
    else:
        st.info("No services affected yet.")
        
    st.markdown("---")
    
    st.subheader("Score Timeline")
    with st.container(border=True):
        fig_score = charts.generate_score_timeline(engine)
        st.plotly_chart(fig_score, use_container_width=True, key=f"score_chart_{len(engine.processed_events)}")

    st.markdown("---")
    
    col_sys, col_spof = st.columns(2)
    
    with col_sys:
        st.subheader("Affected Systems")
        affected = []
        for sys_id, state in engine.system_states.items():
            if state.effective_availability < 1.0:
                affected.append({
                    "System ID": sys_id,
                    "Availability": f"{state.effective_availability * 100:.1f}%"
                })
        with st.container(border=True):
            if affected:
                st.dataframe(affected, use_container_width=True)
            else:
                st.info("All systems healthy.")
            
    with col_spof:
        st.subheader("Recommendations & SPOF")
        with st.container(border=True):
            # In a full implementation, we'd query GraphAnalysis for articulation points.
            # For Milestone 2, we can just list the known SPOFs from the demo graph.
            st.info("💡 **Recommendation**: Primary Database is a Single Point of Failure (SPOF) for Payment Processing. Implement automated failover to the Read Replica.")
            st.info("💡 **Recommendation**: Increase backup frequency to reduce potential RPO breaches.")
        
    st.markdown("---")
    st.subheader("Impact Flow Diagram")
    st.markdown("<p style='color: var(--text-muted);'>Visualizing the technical failure cascading to service degradation and ultimate business outcome.</p>", unsafe_allow_html=True)
    with st.container(border=True):
        fig_flow = charts.generate_impact_flow(engine)
        st.plotly_chart(fig_flow, use_container_width=True, key=f"impact_flow_{len(engine.processed_events)}")
