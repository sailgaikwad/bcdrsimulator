import pytest
from app.models.organization import BusinessService
from app.models.system import System
from app.models.enums import SystemType, DependencyType, StrategyType
from app.graph.dependency_graph import DependencyGraph
from app.models.dependency import Dependency
from app.models.simulation import SimulationRun, ResourcePool
from app.core.simulation_engine import SimulationEngine
from app.models.recovery import RecoveryStrategy
from app.models.disaster import DisasterScenario, AffectedSystem
from app.visualization.network_graph import generate_plotly_graph
from app.database.sqlite_manager import SQLiteManager

def test_dependency_graph_rendering_states():
    db = SQLiteManager(":memory:")
    db.initialize()
    
    g = DependencyGraph()
    sys1 = System(id="sys-db-pri", org_id="org1", name="Primary DB", system_type=SystemType.DATABASE)
    sys2 = System(id="sys-app", org_id="org1", name="App Cluster", system_type=SystemType.APPLICATION)
    
    g.add_system(sys1)
    g.add_system(sys2)
    g.add_dependency(Dependency(id="dep1", org_id="org1", source_id="sys-db-pri", target_id="sys-app", type=DependencyType.HARD))
    
    run_data = SimulationRun(id="run1", org_id="org1", scenario_id="scen1", rng_seed=42)
    pool = ResourcePool(team_capacity=5, budget_remaining=1000.0)
    engine = SimulationEngine(run_data, g, [], {}, pool)
    
    # Test E: Reset simulation -> graph returns to initial healthy state
    fig = generate_plotly_graph(engine, db)
    colors = fig.data[-1].marker.color
    assert all(c == 'green' for c in colors), "Graph should initially be completely green"
    
    # Test A: Trigger disaster
    engine.trigger_disaster({"sys-db-pri": 1.0})
    fig = generate_plotly_graph(engine, db)
    colors = fig.data[-1].marker.color
    texts = fig.data[-1].text
    node_to_color = dict(zip(texts, colors))
    
    assert node_to_color["sys-db-pri"] == 'red', "Primary DB should be red after disaster"
    assert node_to_color["sys-app"] == 'green', "App cluster should be green before propagation"
    
    # Test B: Process next propagation event
    engine.step()  # Should be the propagation to sys-app
    fig = generate_plotly_graph(engine, db)
    colors = fig.data[-1].marker.color
    node_to_color = dict(zip(fig.data[-1].text, colors))
    
    assert node_to_color["sys-app"] == 'red', "App cluster should be red after propagation"
    
    # Test D: Initiate recovery -> process -> reflects states
    strat = RecoveryStrategy(name="Strat", strategy_type=StrategyType.FAILOVER, optimistic_hours=1, likely_hours=1, pessimistic_hours=1, resource_cost=1, monetary_cost=0)
    plan, evt = engine.recovery.start_recovery("sys-db-pri", strat, engine.current_time)
    engine.schedule_event(evt)
    
    evt_step = engine.step()
    print("STEP 1:", evt_step)
    
    # We step the propagation event
    evt2 = engine.step()
    print("STEP 2:", evt2)
    
    fig = generate_plotly_graph(engine, db)
    colors = fig.data[-1].marker.color
    node_to_color = dict(zip(fig.data[-1].text, colors))
    
    assert node_to_color["sys-db-pri"] == 'green', "Primary DB should be green after recovery"
    assert node_to_color["sys-app"] == 'green', "App cluster should be green after recovery propagation"
