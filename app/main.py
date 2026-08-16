import streamlit as st

# Configure the main Streamlit page
st.set_page_config(
    page_title="BC/DR Simulator",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

from app.ui import state_manager
from app.ui import dashboard
from app.ui import infrastructure
from app.ui import dependency_graph
from app.ui import scenarios
from app.ui import simulation
from app.ui import recovery
from app.ui import risk
from app.ui import bia

def render_sidebar():
    st.sidebar.title("BC/DR Simulator")
    st.sidebar.markdown("---")
    
    # We use radio buttons for custom routing to maintain tight control over state
    page = st.sidebar.radio("Navigation", [
        "Dashboard",
        "Infrastructure",
        "Dependency Graph",
        "Disaster Scenarios",
        "Simulation",
        "Recovery Planning",
        "Strategy Comparison",
        "Risk Analysis",
        "Business Impact Analysis",
        "Historical Runs",
    ])
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("Reset Simulation"):
        state_manager.reset_simulation()
        st.rerun()

    return page

def main():
    # Inject global styles
    from app.ui import styles
    styles.inject_custom_css()

    # Ensure database and simulation engines are loaded into session state
    state_manager.init_session_state()

    page = render_sidebar()

    # Routing
    if page == "Dashboard":
        dashboard.render()
    elif page == "Infrastructure":
        infrastructure.render()
    elif page == "Dependency Graph":
        dependency_graph.render()
    elif page == "Disaster Scenarios":
        scenarios.render()
    elif page == "Simulation":
        simulation.render()
    elif page == "Recovery Planning":
        recovery.render()
    elif page == "Strategy Comparison":
        import app.ui.strategy_comparison as strategy_comparison
        strategy_comparison.render()
    elif page == "Risk Analysis":
        risk.render()
    elif page == "Business Impact Analysis":
        bia.render()
    elif page == "Historical Runs":
        import app.ui.history as history
        history.render()

if __name__ == "__main__":
    main()
