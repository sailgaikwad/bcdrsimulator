import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from app.core.simulation_engine import SimulationEngine

def generate_score_timeline(engine: SimulationEngine) -> go.Figure:
    """Generates a line chart tracking the resilience score over time."""
    ledger = engine.scoring.get_ledger()
    if not ledger:
        return go.Figure()
        
    times = [0.0]
    scores = [100.0]  # Base score
    
    current_score = 100.0
    for evt in ledger:
        current_score += evt.delta
        times.append(evt.event_time)
        scores.append(current_score)
        
    # Append current time to extend line
    if times[-1] < engine.current_time:
        times.append(engine.current_time)
        scores.append(current_score)
        
    fig = px.line(x=times, y=scores, markers=True, title="Composite Resilience Score Timeline")
    fig.update_layout(
        xaxis_title="Simulation Time (Hours)",
        yaxis_title="Score",
        yaxis_range=[0, 100]
    )
    return fig


def generate_rto_comparison(engine: SimulationEngine) -> go.Figure:
    """Generates a bar chart comparing actual downtime against Target RTO and MTPD."""
    services = []
    rto = []
    mtpd = []
    actual = []
    
    for svc in engine.services:
        impact = engine.bia.get_impact(svc.id)
        if impact:
            services.append(svc.name)
            rto.append(svc.rto_hours)
            mtpd.append(svc.mtpd_hours)
            actual.append(impact.downtime_hours)
            
    if not services:
        return go.Figure()

    fig = go.Figure(data=[
        go.Bar(name='Target RTO', x=services, y=rto, marker_color='green'),
        go.Bar(name='MTPD (Max)', x=services, y=mtpd, marker_color='orange'),
        go.Bar(name='Actual Downtime', x=services, y=actual, marker_color='red')
    ])
    
    fig.update_layout(
        barmode='group',
        title="RTO and MTPD vs Actual Downtime",
        yaxis_title="Hours"
    )
    return fig


def generate_impact_flow(engine: SimulationEngine) -> go.Figure:
    """
    Generates a Sankey diagram tracing Technical Failure -> Service Impact -> Business Outcome.
    """
    # Nodes: Systems -> Services -> Outcome (Operational/Failed)
    labels = []
    sources = []
    targets = []
    values = []
    
    # Map for node indexing
    node_idx = {}
    
    def get_node(name: str):
        if name not in node_idx:
            node_idx[name] = len(labels)
            labels.append(name)
        return node_idx[name]

    # Collect failed/degraded systems
    for sys_id, state in engine.system_states.items():
        if state.effective_availability < 1.0:
            s_idx = get_node(sys_id)
            
            # Find mapped services
            for svc in engine.services:
                if sys_id in engine.bia.service_systems_map.get(svc.id, []):
                    svc_idx = get_node(svc.name)
                    sources.append(s_idx)
                    targets.append(svc_idx)
                    values.append(1) # Weight of flow
                    
                    # Target outcome for this service
                    impact = engine.bia.get_impact(svc.id)
                    if impact and impact.mtpd_breached:
                        out_idx = get_node("BUSINESS FAILURE")
                    else:
                        out_idx = get_node("OPERATIONAL")
                        
                    sources.append(svc_idx)
                    targets.append(out_idx)
                    values.append(1)

    if not sources:
        return go.Figure()

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values
        )
    )])
    
    fig.update_layout(title_text="Technical -> Service -> Business Impact Flow", font_size=10)
    return fig


def generate_timeline_gantt(engine: SimulationEngine) -> go.Figure:
    """Generates a Gantt chart of failure and recovery periods."""
    tasks = []
    
    # We use engine.system_states to trace failure and recovery times.
    # Note: For Milestone 2, we just plot the current degraded state.
    # A full Gantt requires tracing historical state changes which are currently in the events ledger.
    # We'll extract failure starts from the ledger.
    
    ledger = engine.scoring.get_ledger()
    failure_starts = {}
    recovery_starts = {}
    
    # Very rudimentary parsing of the ledger to build the timeline
    for evt in ledger:
        # Example logic, depends on reason string for now (technical debt for M3)
        pass
        
    # For now, show active downtimes
    for sys_id, state in engine.system_states.items():
        if state.failed_at is not None:
            end_time = engine.current_time
            if state.restored_at is not None:
                end_time = state.restored_at
                
            tasks.append(dict(
                Task=sys_id, 
                Start=state.failed_at, 
                Finish=end_time, 
                Resource="Failed"
            ))

    if not tasks:
        return go.Figure()
        
    # Convert numerical time to a pseudo-datetime for Plotly timeline (since it requires dates)
    import datetime
    base_date = datetime.datetime(2025, 1, 1)
    
    for t in tasks:
        t["Start"] = base_date + datetime.timedelta(hours=t["Start"])
        t["Finish"] = base_date + datetime.timedelta(hours=t["Finish"])
        
    df = pd.DataFrame(tasks)
    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Resource", title="System Downtime Timeline")
    
    # Format x-axis back to hours if needed, or leave as date
    fig.update_yaxes(autorange="reversed") 
    return fig
