import streamlit as st

def render():
    st.header("Risk Analysis")
    
    st.markdown("""
    This module performs quantitative risk evaluation using the `P × I × E` model:
    - **P (Probability)**: Likelihood of the event occurring (0.0 to 1.0)
    - **I (Impact)**: Financial or operational severity
    - **E (Exposure)**: Percentage of the organization affected
    """)
    
    # In Milestone 1, we show a basic example based on the loaded FinServe demo services.
    # In later milestones, this will connect deeply to the RiskEngine.
    
    if "engine" not in st.session_state:
        st.warning("Engine not initialized.")
        return
        
    engine = st.session_state["engine"]
    
    st.subheader("High Level Risk Exposure (Mock Data for M1)")
    
    # Simple risk table based on services
    risk_data = []
    for svc in engine.services:
        # Fictional static risk params for the demo
        prob = 0.05
        impact = svc.revenue_per_hour * svc.mtpd_hours
        exposure = svc.criticality / 10.0
        
        score = prob * impact * exposure
        
        category = "CRITICAL" if score > 5000 else "HIGH" if score > 1000 else "MEDIUM"
        
        risk_data.append({
            "Risk Source": svc.name,
            "Probability": f"{prob*100:.1f}%",
            "Impact (Max Loss)": f"INR {impact:,.2f}",
            "Exposure": f"{exposure*100:.1f}%",
            "P×I×E Score": f"{score:,.2f}",
            "Category": category
        })
        
    st.dataframe(risk_data, use_container_width=True)
    
    st.info("The Risk Engine continuously monitors the architecture graph for Single Points of Failure (SPOF) to recalculate Exposure automatically.")
