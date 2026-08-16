from streamlit.testing.v1 import AppTest
import pytest
import os

# Ensure the database exists for tests by running state init
@pytest.fixture(autouse=True)
def setup_db():
    if os.path.exists("bcdr.db"):
        os.remove("bcdr.db")
    yield
    if os.path.exists("bcdr.db"):
        os.remove("bcdr.db")

def test_app_loads_successfully():
    """Verify that the Streamlit app loads and the FinServe demo initializes without errors."""
    at = AppTest.from_file("../app/main.py").run()
    assert not at.exception, "App crashed on startup"
    
    # Check default page (Dashboard)
    assert "Dashboard" in at.title[0].value or "Dashboard" in at.header[0].value

def test_navigation():
    """Test switching between pages."""
    at = AppTest.from_file("../app/main.py").run()
    
    # Simulate clicking "Simulation" in the sidebar
    at.sidebar.radio[0].set_value("Simulation").run()
    assert not at.exception
    assert "Simulation Engine Control" in at.header[0].value

def test_trigger_disaster():
    """Test triggering a disaster via the UI."""
    at = AppTest.from_file("../app/main.py").run()
    
    at.sidebar.radio[0].set_value("Simulation").run()
    
    # Find the trigger disaster button and click it
    trigger_btn = None
    for btn in at.button:
        if "Trigger Disaster" in btn.label:
            trigger_btn = btn
            break
            
    assert trigger_btn is not None
    assert not trigger_btn.disabled
    
    trigger_btn.click().run()
    assert not at.exception

def test_historical_runs_empty_state():
    """Test Historical Runs page empty state."""
    at = AppTest.from_file("../app/main.py").run()
    at.sidebar.radio[0].set_value("Historical Runs").run()
    
    assert not at.exception
    assert "Historical Runs" in at.header[0].value
    assert any("No historical runs found" in i.value for i in at.info)

def test_strategy_comparison_load():
    """Test Strategy Comparison page loads."""
    at = AppTest.from_file("../app/main.py").run()
    at.sidebar.radio[0].set_value("Strategy Comparison").run()
    
    assert not at.exception
    assert "Recovery Strategy Comparison" in at.header[0].value

def test_impact_flow_regression():
    """Regression test for the Impact Flow charts rendering after a disaster step."""
    at = AppTest.from_file("../app/main.py").run()
    
    # 1. Trigger Disaster
    at.sidebar.radio[0].set_value("Simulation").run()
    trigger_btn = next((b for b in at.button if "Trigger Disaster" in b.label), None)
    trigger_btn.click().run()
    
    # 2. Step Simulation
    step_btn = next((b for b in at.button if "Step (+30m)" in b.label), None)
    if step_btn:
        step_btn.click().run()
    
    # 3. View Dashboard
    at.sidebar.radio[0].set_value("Dashboard").run()
    
    assert not at.exception

def test_recovery_planning_integration():
    """Bug 1 Regression: Ensure recovery planning doesn't crash from resource_pool reference."""
    at = AppTest.from_file("../app/main.py").run()
    
    # 1. Trigger Disaster
    at.sidebar.radio[0].set_value("Simulation").run()
    trigger_btn = next((b for b in at.button if "Trigger Disaster" in b.label), None)
    if trigger_btn:
        trigger_btn.click().run()
        
    # No step_btn needed because primary DB fails immediately
    at.sidebar.radio[0].set_value("Recovery Planning").run()
    assert not at.exception
    assert "Recovery Planning" in at.header[0].value
    assert any("Current Resource Pool" in sh.value for sh in at.subheader)

def test_strategy_comparison_sampling():
    """Bug 2 Regression: Ensure Strategy Comparison uses correct RNG API."""
    at = AppTest.from_file("../app/main.py").run()
    at.sidebar.radio[0].set_value("Strategy Comparison").run()
    assert not at.exception
    assert "Recovery Strategy Comparison" in at.header[0].value
    # If the sampled_duration accessor failed, it would throw an exception by now.

def test_save_run_foreign_key_integrity():
    """Bug 3 Regression: Ensure Saving a Run doesn't violate scenarios FK constraint."""
    at = AppTest.from_file("../app/main.py").run()
    at.sidebar.radio[0].set_value("Simulation").run()
    
    trigger_btn = next((b for b in at.button if "Trigger Disaster" in b.label), None)
    if trigger_btn:
        trigger_btn.click().run(timeout=10)
    
    # Bypass UI to avoid timeout
    at.session_state["engine"].run_until_empty()
    at.run()
    
    save_run_btn = next((b for b in at.button if "Save Run" in b.label), None)
    if save_run_btn:
        save_run_btn.click().run(timeout=10)
        
    for e in at.error:
        print("ERROR:", e.value)
    for e in at.exception:
        print("EXCEPTION:", e)
        
    assert not at.exception
    
    # Verify in DB
    from app.database.sqlite_manager import SQLiteManager
    db = SQLiteManager("bcdr.db")
    with db.connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM simulation_runs").fetchone()[0]
        assert count > 0
