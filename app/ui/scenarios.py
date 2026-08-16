import streamlit as st
from app.models.disaster import DisasterScenario, AffectedSystem
from app.models.enums import DisasterCategory
from app.database.repositories import DisasterScenarioRepository
from app.ui.state_manager import reset_simulation

def render():
    st.header("Disaster Scenarios")

    db = st.session_state.get("db")
    if not db:
        st.warning("Database not initialized.")
        return

    repo = DisasterScenarioRepository(db)
    scenarios = repo.list_all()

    if not scenarios:
        st.warning("No scenarios available.")
        return

    st.subheader("Available Scenarios")

    options = {s.name: s for s in scenarios}

    current_scenario = st.session_state.get("active_scenario")
    current_index = 0
    if current_scenario:
        for i, s in enumerate(scenarios):
            if s.id == current_scenario.id:
                current_index = i
                break

    selected_name = st.selectbox("Select Scenario to Review", list(options.keys()), index=current_index)
    selected_scenario: DisasterScenario = options[selected_name]

    if not current_scenario or current_scenario.id != selected_scenario.id:
        st.session_state["active_scenario"] = selected_scenario
        reset_simulation()

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
