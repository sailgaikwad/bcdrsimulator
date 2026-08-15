import streamlit as st

def render():
    st.header("Business Impact Analysis (BIA)")
    
    st.markdown("""
    This page tracks the financial and operational impact of downtime on the organization's business services.
    
    ### Recovery Definitions
    - **Technical Recovery (RTO_t):** The time required to restore the underlying IT infrastructure (servers, databases, networks).
    - **Work Recovery Time (WRT):** The time required by the business to verify data, clear backlogs, and resume normal operations *after* technical recovery.
    - **Service/Business Recovery (RTO_b):** Total time to resume business operations (`RTO_t + WRT`).
    """)
    
    st.warning("⚠️ **Note:** Work Recovery Time (WRT) is currently implemented as a fixed global value of `2.0h` across all services. In future milestones, this will become configurable per `BusinessService`.")
    
    if "engine" not in st.session_state:
        st.warning("Engine not initialized.")
        return
        
    engine = st.session_state["engine"]
    
    st.subheader("Current Business Impact Status")
    
    bia_data = []
    for svc in engine.services:
        impact = engine.bia.get_impact(svc.id)
        if impact:
            mtpd_breached = "YES" if impact.mtpd_breached else "NO"
            bia_data.append({
                "Service": svc.name,
                "Current Downtime": f"{impact.downtime_hours:.2f}h",
                "Target RTO": f"{svc.rto_hours}h",
                "Target MTPD": f"{svc.mtpd_hours}h",
                "Revenue Lost": f"INR {impact.revenue_lost:,.2f}",
                "MTPD Breached": mtpd_breached
            })
            
    if bia_data:
        st.dataframe(bia_data, use_container_width=True)
    else:
        st.info("No services have registered downtime yet. Trigger the disaster to begin tracking impact.")
