import streamlit as st
from app.core.simulation_engine import SimulationEngine
from app.models.recovery import RecoveryStrategy
from app.models.enums import DependencyType

def render():
    st.header("Recovery Planning & Execution")
    
    if "engine" not in st.session_state:
        st.warning("Engine not initialized.")
        return
        
    engine: SimulationEngine = st.session_state["engine"]
    strategies = st.session_state.get("recovery_strategies", [])
    
    st.markdown("Select a degraded/failed system and initiate a recovery strategy.")
    
    # Filter for systems that actually need recovery
    failed_systems = [
        sys_id for sys_id, state in engine.system_states.items()
        if state.effective_availability < 1.0
    ]
    
    if not failed_systems:
        st.success("All systems are currently healthy. No recovery actions needed.")
        return
        
    target_sys = st.selectbox("Select Target System", failed_systems)
    
    # Check upstream health
    blocked_by = []
    for upstream_id, edge_data in engine.dep_graph.get_upstream(target_sys):
        dep_type = edge_data.get("dep_type", "hard")
        if dep_type in [DependencyType.HARD.value, DependencyType.HARD, DependencyType.DATA_SYNC.value, DependencyType.DATA_SYNC]:
            upstream_state = engine.system_states.get(upstream_id)
            if upstream_state and upstream_state.effective_availability < 1.0:
                blocked_by.append(upstream_id)
                
    if blocked_by:
        st.error(f"Recovery of {target_sys} is blocked. Critical upstream dependencies must be recovered first: {', '.join(blocked_by)}")
    
    # Display Strategies
    st.subheader("Available Strategies")
    
    if not strategies:
        st.info("No recovery strategies found.")
        return
        
    strat_names = [s.name for s in strategies]
    selected_name = st.selectbox("Select Strategy", strat_names)
    selected_strat: RecoveryStrategy = next(s for s in strategies if s.name == selected_name)
    
    # Strategy Details
    st.write(f"**Type:** {selected_strat.strategy_type.value}")
    st.write(f"**Estimated Duration (Pessimistic):** {selected_strat.pessimistic_hours} hours")
    st.write(f"**Resource Cost (Team):** {selected_strat.resource_cost}")
    st.write(f"**Monetary Cost:** INR {selected_strat.monetary_cost:,.2f}")
    
    st.markdown("---")
    
    # Action
    is_disabled = len(blocked_by) > 0
    if st.button("Initiate Recovery", type="primary", disabled=is_disabled):
        if target_sys in engine.recovery._active_plans:
            st.warning("A recovery is already active for this system.")
        else:
            # We start recovery. The engine will sample the exact duration probabilistically.
            plan, evt = engine.recovery.start_recovery(target_sys, selected_strat, engine.current_time)
            
            if plan:
                st.success("Recovery plan accepted by constraints.")
                st.write(f"**Sampled Recovery Duration:** {plan.actual_duration:.2f} hours")
                st.info("The recovery completion event has been scheduled. Head to the **Simulation** tab and step the simulation to complete the recovery.")
                engine.schedule_event(evt)
            else:
                st.error("Recovery plan rejected! (Resource constraints exceeded)")
            
    st.markdown("---")
    st.subheader("Current Resource Pool")
    st.write(f"**Available Team Capacity:** {engine.recovery.resource_pool.team_capacity}")
    st.write(f"**Budget Remaining:** INR {engine.recovery.resource_pool.budget_remaining:,.2f}")
