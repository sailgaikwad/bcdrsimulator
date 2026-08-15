import streamlit as st
from app.models.disaster import DisasterScenario, AffectedSystem
from app.models.enums import DisasterCategory

def render():
    st.header("Disaster Scenarios")
    
    if "active_scenario" not in st.session_state:
        st.warning("No scenario loaded.")
        return
        
    current = st.session_state["active_scenario"]
    
    st.subheader("Available Scenarios")
    
    # In a full app, this would query a ScenarioRepository.
    # For Milestone 1 demo, we mock the selection.
    options = {
        "Primary Database Failure": current
    }
    
    selected_name = st.selectbox("Select Scenario to Review", list(options.keys()))
    selected_scenario: DisasterScenario = options[selected_name]
    
    st.markdown("---")
    st.subheader(f"Scenario Details: {selected_scenario.name}")
    st.write(f"**Category:** {selected_scenario.category.value}")
    st.write(f"**Base Severity:** {selected_scenario.severity}")
    
    st.write("**Affected Systems:**")
    affected_data = []
    for a in selected_scenario.affected_systems:
        affected_data.append({
            "System ID": a.system_id,
            "Health Impact": f"{a.health_impact * 100}%",
            "Delay (hrs)": a.delay_hours
        })
    st.table(affected_data)
    
    st.info("Head to the **Simulation** tab to trigger this scenario and watch the cascade.")
