import streamlit as st
from app.core.simulation_engine import SimulationEngine
from app.models.recovery import RecoveryStrategy

def render():
    st.header("Recovery Strategy Comparison")
    
    if "engine" not in st.session_state:
        st.warning("Engine not initialized.")
        return
        
    engine: SimulationEngine = st.session_state["engine"]
    strategies = st.session_state.get("recovery_strategies", [])
    
    if not strategies:
        st.info("No recovery strategies available.")
        return
        
    st.markdown("Compare the projected outcomes of applying different recovery strategies to a failed system.")
    
    failed_systems = [
        sys_id for sys_id, state in engine.system_states.items()
        if state.effective_availability < 1.0
    ]
    
    if not failed_systems:
        st.success("All systems are currently healthy. Trigger a disaster to run a comparison.")
        return
        
    target_sys = st.selectbox("Select Target Failed System", failed_systems)
    
    st.markdown("---")
    
    comparison_data = []
    
    for strat in strategies:
        # Simulate what would happen if we chose this strategy right now
        # We temporarily grab the exact deterministic sampled duration by calling the engine's planner
        # We don't want to actually commit it to the schedule, so we use the RecoveryEngine's
        # internal method _sample_duration
        
        # We need to compute potential business outcome if this duration applies
        sampled_dur = engine.recovery._sample_duration(strat)
        
        # We can see if it fits in budget
        can_afford = engine.resource_pool.can_start_recovery(strat.resource_cost, strat.monetary_cost)
        
        comparison_data.append({
            "Strategy": strat.name,
            "Type": strat.strategy_type.value,
            "Expected Range": f"{strat.optimistic_hours}h - {strat.pessimistic_hours}h",
            "Sampled Duration": f"{sampled_dur:.2f}h",
            "Resource Cost": strat.resource_cost,
            "Monetary Cost": f"INR {strat.monetary_cost:,.2f}",
            "Can Afford?": "Yes" if can_afford else "No",
            "Data Loss (RPO Impact)": f"{strat.data_loss_hours}h"
        })
        
    st.subheader("Strategy Profiles & Sampling")
    st.table(comparison_data)
    
    st.info("The 'Sampled Duration' is a deterministic projection of the actual time it will take if you initiate this strategy now, based on the simulation RNG seed.")
