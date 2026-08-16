import streamlit as st

def render():
    st.header("Risk Register")
    st.markdown("<p style='color: var(--text-muted);'>View and analyze organizational risks and their mitigations.</p>", unsafe_allow_html=True)
    
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
    risks = getattr(engine, "risks", [])
    
    with st.container(border=True):
        st.subheader("Active Risks")
        if not risks:
            st.info("No risks registered.")
        else:
            risk_data = []
            for r in risks:
                risk_data.append({
                    "Risk ID": r.id,
                    "Description": r.description,
                    "Likelihood": r.likelihood.value,
                    "Impact": r.impact.value,
                    "Score": f"{r.get_risk_score():.1f}",
                    "Status": r.status.value
                })
                
            import pandas as pd
            st.dataframe(pd.DataFrame(risk_data), use_container_width=True)
    
    st.info("The Risk Engine continuously monitors the architecture graph for Single Points of Failure (SPOF) to recalculate Exposure automatically.")
