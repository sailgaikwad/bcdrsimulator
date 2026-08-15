import streamlit as st
from app.visualization.network_graph import generate_plotly_graph
from app.core.simulation_engine import SimulationEngine

def render():
    st.header("Dependency Graph")
    
    if "engine" not in st.session_state or "db" not in st.session_state:
        st.warning("Engine or DB not initialized.")
        return
        
    engine: SimulationEngine = st.session_state["engine"]
    db = st.session_state["db"]
    
    st.markdown("Interactive visualization of the current dependency network and health status.")
    
    fig = generate_plotly_graph(engine, db)
    st.plotly_chart(fig, use_container_width=True)
    
    st.info("🟢 Healthy (100%) | 🟠 Degraded (1-99%) | 🔴 Failed (0%)")
