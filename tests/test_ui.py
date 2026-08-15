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
