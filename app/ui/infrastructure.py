import streamlit as st
from app.database.sqlite_manager import SQLiteManager
from app.database.repositories import SystemRepository, BusinessServiceRepository, DependencyRepository

def render():
    st.header("Infrastructure & Services")
    
    if "db" not in st.session_state:
        st.warning("Database not initialized.")
        return
        
    db: SQLiteManager = st.session_state["db"]
    org_id = "org-finserve" # Hardcoded for demo
    
    sys_repo = SystemRepository(db)
    svc_repo = BusinessServiceRepository(db)
    dep_repo = DependencyRepository(db)
    
    services = svc_repo.list_by_org(org_id)
    systems = sys_repo.list_by_org(org_id)
    deps = dep_repo.list_by_org(org_id)
    
    st.subheader("Business Services")
    if services:
        svc_data = [{
            "Name": s.name,
            "Criticality": s.criticality,
            "RTO (hours)": s.rto_hours,
            "RPO (hours)": s.rpo_hours,
            "MTPD (hours)": s.mtpd_hours,
            "Revenue/hr": f"INR {s.revenue_per_hour:,.2f}"
        } for s in services]
        st.dataframe(svc_data, use_container_width=True)
    else:
        st.info("No business services defined.")
        
    st.markdown("---")
        
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Systems Inventory")
        if systems:
            sys_data = [{
                "Name": s.name,
                "Type": s.system_type.value,
                "Tier": s.tier.value
            } for s in systems]
            st.dataframe(sys_data, use_container_width=True)
        else:
            st.info("No systems defined.")
            
    with col2:
        st.subheader("Dependencies")
        if deps:
            dep_data = [{
                "Source": sys_repo.get(d.source_id).name if sys_repo.get(d.source_id) else d.source_id,
                "Target": sys_repo.get(d.target_id).name if sys_repo.get(d.target_id) else d.target_id,
                "Type": d.dep_type.value,
                "Weight": d.weight
            } for d in deps]
            st.dataframe(dep_data, use_container_width=True)
        else:
            st.info("No dependencies defined.")
