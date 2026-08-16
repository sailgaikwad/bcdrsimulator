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
    # Use a dynamic key based on processed events to force Streamlit to redraw the Plotly component
    # when the simulation state changes, bypassing shallow React/Plotly diffing bugs.
    dynamic_key = f"dep_graph_{len(engine.processed_events)}"
    st.plotly_chart(fig, use_container_width=True, key=dynamic_key)
    
    st.info("🟢 Healthy (100%) | 🔵 Recovering | 🟠 Degraded | 🔴 Failed (0%) &nbsp;&nbsp; **Edges:** ─── Hard | - - Sync | ··· Disrupted")
