import sys
import os

# Add local path to sys.path
sys.path.insert(0, os.path.abspath("."))

from app.database.sqlite_manager import SQLiteManager
from app.ui.state_manager import _init_simulation_engine
from app.visualization.network_graph import generate_plotly_graph
import streamlit as st

class DummySession(dict):
    def __getattr__(self, item):
        return self[item]
    def __setattr__(self, key, value):
        self[key] = value

st.session_state = DummySession()
db = SQLiteManager("bcdr.db")
db.initialize()
st.session_state["db"] = db
_init_simulation_engine()

engine = st.session_state["engine"]
db = st.session_state["db"]
scenario = st.session_state["active_scenario"]

def check_graph_colors(stage):
    fig = generate_plotly_graph(engine, db)
    # The nodes are in fig.data[2]
    node_trace = fig.data[2]
    print(f"\n--- {stage} ---")
    for text, color in zip(node_trace.text, node_trace.marker.color):
        print(f"{text}: {color}")
    print(f"App state avail: {engine.system_states['sys-app'].effective_availability}")
    print(f"Primary DB avail: {engine.system_states['sys-db-pri'].effective_availability}")

check_graph_colors("Initial")

impacts = {a.system_id: a.health_impact for a in scenario.affected_systems}
engine.trigger_disaster(impacts)
check_graph_colors("After Trigger Disaster")

evt = engine.step()
print(f"\nExecuted Event: {evt.event_type.name} on {evt.system_id}")
check_graph_colors("After Step 1")
