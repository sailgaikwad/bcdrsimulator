import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from app.core.simulation_engine import SimulationEngine

def generate_score_timeline(engine: SimulationEngine) -> go.Figure:
    """
    Generates a line chart tracking the resilience score over time.

    Replays the ledger chronologically, maintaining per-category running totals
    and computing a weighted composite score at each event — identical to the
    logic in ScoringEngine.get_composite_score(). This ensures the final point
    on the chart always matches the Resilience Score shown on the Dashboard.
    """
    from app.core.scoring import CATEGORY_WEIGHTS
    from app.models.enums import ScoreCategory

    ledger = engine.scoring.get_ledger()
    if not ledger:
        return go.Figure()

    _BASE_SCORE = 100.0

    # Per-category running totals, starting at base
    category_totals: dict = {cat: _BASE_SCORE for cat in ScoreCategory}

    def _composite(totals: dict) -> float:
        total = 0.0
        for cat, weight in CATEGORY_WEIGHTS.items():
            total += max(0.0, min(100.0, totals[cat])) * weight
        return round(total, 2)

    times = [0.0]
    scores = [_composite(category_totals)]  # Starting composite (100.0)

    for evt in ledger:
        category_totals[evt.category] += evt.delta
        times.append(evt.event_time)
        scores.append(_composite(category_totals))

    # Extend the line to the current simulation clock if no recent events
    if times[-1] < engine.current_time:
        times.append(engine.current_time)
        scores.append(scores[-1])

    final_score = engine.scoring.get_composite_score()

    fig = px.line(x=times, y=scores, markers=True, title="Composite Resilience Score Timeline", color_discrete_sequence=["#3b82f6"])
    fig.add_hline(
        y=final_score,
        line_dash="dot",
        line_color="#3b82f6",
        annotation_text=f"Current: {final_score:.1f}",
        annotation_position="bottom right",
    )
    fig.update_layout(
        xaxis_title="Simulation Time (Hours)",
        yaxis_title="Score",
        yaxis_range=[0, 100],
        font=dict(family="Inter, sans-serif"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(0,0,0,0.05)"),
        yaxis=dict(gridcolor="rgba(0,0,0,0.05)")
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
        go.Bar(name='Target RTO', x=services, y=rto, marker_color='#10b981'),
        go.Bar(name='MTPD (Max)', x=services, y=mtpd, marker_color='#f59e0b'),
        go.Bar(name='Actual Downtime', x=services, y=actual, marker_color='#f43f5e')
    ])
    
    fig.update_layout(
        barmode='group',
        title="RTO and MTPD vs Actual Downtime",
        yaxis_title="Hours",
        font=dict(family="Inter, sans-serif"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="rgba(0,0,0,0.05)")
    )
    return fig


def generate_impact_flow(engine: SimulationEngine) -> go.Figure:
    """
    Generates a clear, multi-panel impact dashboard replacing the ambiguous Sankey.

    Layout:
      - Top panel: System Health Loss — horizontal bar per system showing % health lost
      - Bottom panel: Service Business Impact — grouped bars of downtime vs RTO vs MTPD,
        annotated with revenue lost
    """
    from app.database.repositories import SystemRepository

    # ── Gather system health data ──────────────────────────────────────────────
    sys_names = []
    health_lost_pct = []
    sys_colors = []

    for sys_id, state in engine.system_states.items():
        avail = state.effective_availability
        loss = (1.0 - avail) * 100.0
        if loss <= 0.0:
            continue  # Skip fully healthy systems

        # Use node data stored in graph for the name
        node_data = engine.dep_graph.get_node_data(sys_id)
        name = node_data.get("name", sys_id) if node_data else sys_id
        sys_names.append(name)
        health_lost_pct.append(round(loss, 1))

        sys_colors.append("#f59e0b")  # Amber

    # ── Gather service business impact data ───────────────────────────────────
    svc_names = []
    svc_downtime = []
    svc_rto = []
    svc_mtpd = []
    svc_revenue = []
    svc_bar_colors = []

    for svc in engine.services:
        impact = engine.bia.get_impact(svc.id)
        if not impact or impact.downtime_hours <= 0:
            continue
        svc_names.append(svc.name)
        svc_downtime.append(round(impact.downtime_hours, 2))
        svc_rto.append(svc.rto_hours)
        svc_mtpd.append(svc.mtpd_hours)
        svc_revenue.append(impact.revenue_lost)
        svc_bar_colors.append("#f43f5e") # Rose

    if not sys_names and not svc_names:
        fig = go.Figure()
        fig.update_layout(
            title="Impact Flow — No failures detected yet",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    from plotly.subplots import make_subplots

    has_sys = bool(sys_names)
    has_svc = bool(svc_names)
    rows = (1 if has_sys else 0) + (1 if has_svc else 0)
    if rows == 0:
        return go.Figure()

    subplot_titles = []
    if has_sys:
        subplot_titles.append("System Health Loss (% capacity lost)")
    if has_svc:
        subplot_titles.append("Service Business Impact (hours)")

    fig = make_subplots(
        rows=rows,
        cols=1,
        subplot_titles=subplot_titles,
        vertical_spacing=0.18,
        row_heights=[0.45, 0.55][:rows],
    )

    current_row = 1

    # ── Panel 1: System health loss bars ──────────────────────────────────────
    if has_sys:
        # Sort by loss descending
        paired = sorted(zip(health_lost_pct, sys_names, sys_colors), reverse=True)
        health_lost_pct_s, sys_names_s, sys_colors_s = zip(*paired)

        fig.add_trace(
            go.Bar(
                x=list(health_lost_pct_s),
                y=list(sys_names_s),
                orientation="h",
                marker=dict(color=list(sys_colors_s), line=dict(width=0)),
                text=[f"{v:.0f}% lost" for v in health_lost_pct_s],
                textposition="inside",
                insidetextanchor="middle",
                name="Health Lost",
                hovertemplate="<b>%{y}</b><br>Health lost: %{x:.1f}%<extra></extra>",
            ),
            row=current_row, col=1,
        )
        fig.update_xaxes(
            range=[0, 100], ticksuffix="%",
            gridcolor="rgba(0,0,0,0.05)",
            row=current_row, col=1,
        )
        fig.update_yaxes(gridcolor="rgba(0,0,0,0)", row=current_row, col=1)
        current_row += 1

    # ── Panel 2: Service impact grouped bars ──────────────────────────────────
    if has_svc:
        fig.add_trace(
            go.Bar(
                name="RTO Target",
                x=svc_names,
                y=svc_rto,
                marker_color="#10b981",
                opacity=0.85,
                hovertemplate="<b>%{x}</b><br>RTO target: %{y:.1f}h<extra></extra>",
            ),
            row=current_row, col=1,
        )
        fig.add_trace(
            go.Bar(
                name="MTPD Limit",
                x=svc_names,
                y=svc_mtpd,
                marker_color="#8b5cf6",
                opacity=0.85,
                hovertemplate="<b>%{x}</b><br>MTPD limit: %{y:.1f}h<extra></extra>",
            ),
            row=current_row, col=1,
        )
        fig.add_trace(
            go.Bar(
                name="Actual Downtime",
                x=svc_names,
                y=svc_downtime,
                marker_color=svc_bar_colors,
                text=[f"₹{r:,.0f} lost" for r in svc_revenue],
                textposition="auto",          # inside when bar is tall enough, hidden when too small
                constraintext="both",          # never overflow outside the bar or plot
                insidetextanchor="middle",
                textfont=dict(size=10, color="white"),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Downtime: %{y:.2f}h<br>"
                    "Revenue lost: ₹%{customdata:,.0f}<extra></extra>"
                ),
                customdata=svc_revenue,
            ),
            row=current_row, col=1,
        )
        fig.update_yaxes(
            title_text="Hours",
            gridcolor="rgba(0,0,0,0.05)",
            row=current_row, col=1,
        )
        fig.update_xaxes(gridcolor="rgba(0,0,0,0)", row=current_row, col=1)

    fig.update_layout(
        barmode="group",
        title=dict(text="Infrastructure → Service Impact Analysis", font=dict(size=15)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif"),
        # Legend anchored top-right — never overlaps bars regardless of chart width
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
        ),
        margin=dict(t=80, b=30, l=10, r=10),
        height=520 if rows == 2 else 300,
        # No bottom annotation — breach status is already encoded in bar colour
        # and described in the legend entries themselves via hovertext
    )
    return fig



def generate_timeline_gantt(engine: SimulationEngine) -> go.Figure:
    """
    Simulation Timeline — horizontal bar chart showing each system's
    failure, recovery, and restored phases on a real simulation-hour x-axis.

    Phase logic per system:
      - Failed segment   : failed_at  → min(restored_at, recovery_start, current_time)
      - Recovering segment: recovery_start → min(restored_at, current_time)  [if in progress]
      - Restored segment : restored_at → current_time  [if restored]

    Data sources:
      - state.failed_at / state.restored_at  from SystemState
      - engine.recovery._active_plans        for in-progress recovery start times
      - engine.recovery._completed_plans     for completed recovery start times
    """
    if not engine.system_states:
        return go.Figure()

    # Build a lookup: system_id → recovery start time (from active or completed plans)
    recovery_starts: dict[str, float] = {}
    for plan in engine.recovery.get_completed_plans():
        recovery_starts[plan.system_id] = plan.start_time or plan.decision_time or 0.0
    for sys_id, plan in engine.recovery.get_active_plans().items():
        recovery_starts[sys_id] = plan.start_time or plan.decision_time or 0.0

    # Colour palette
    COLOR_FAILED     = "#f43f5e"  # Rose
    COLOR_RECOVERING = "#0ea5e9"  # Sky
    COLOR_RESTORED   = "#10b981"  # Emerald
    COLOR_DEGRADED   = "#f59e0b"  # Amber

    current_t = engine.current_time if engine.current_time > 0 else 0.001

    bar_traces: dict[str, go.Bar] = {}
    y_labels: list[str] = []

    def _add_segment(name: str, t_start: float, t_end: float, color: str, phase: str):
        """Append a single horizontal bar segment."""
        if t_end <= t_start:
            return
        duration = t_end - t_start
        if name not in bar_traces:
            bar_traces[name] = {"phases": []}
        bar_traces[name]["phases"].append({
            "start": t_start, "duration": duration,
            "color": color, "phase": phase,
        })

    for sys_id, state in engine.system_states.items():
        node_data = engine.dep_graph.get_node_data(sys_id)
        label = node_data.get("name", sys_id) if node_data else sys_id
        y_labels.append(label)

        is_recovering = engine.recovery.is_system_recovering(sys_id)
        if is_recovering:
            _add_segment(label, 0.0, current_t, COLOR_RECOVERING, "Recovering")
        elif state.effective_availability >= 1.0:
            _add_segment(label, 0.0, current_t, COLOR_RESTORED, "Healthy")
        elif state.effective_availability <= 0.0:
            _add_segment(label, 0.0, current_t, COLOR_FAILED, "Failed")
        else:
            _add_segment(label, 0.0, current_t, COLOR_DEGRADED, "Degraded")

    if not bar_traces:
        fig = go.Figure()
        fig.update_layout(
            title="Simulation Timeline — No failures recorded yet",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    # ── Build figure with one Bar trace per phase type for legend entries ─────
    # We use a stacked horizontal bar approach:
    #  x = [offset_bar (transparent), duration_bar (coloured)]
    # Plotly doesn't natively do Gantt with continuous hours, so we
    # use base= on go.Bar to replicate offset.

    phase_order = ["Healthy", "Failed", "Degraded", "Recovering", "Restored"]
    phase_colors = {
        "Healthy": COLOR_RESTORED,
        "Failed": COLOR_FAILED,
        "Degraded": COLOR_DEGRADED,
        "Recovering": COLOR_RECOVERING,
        "Restored": COLOR_RESTORED,
    }
    # Group segments by phase across all systems
    phase_data: dict[str, dict] = {p: {"y": [], "base": [], "width": [], "hover": []} for p in phase_order}

    for label, data in bar_traces.items():
        for seg in data["phases"]:
            ph = seg["phase"]
            if ph not in phase_data:
                continue
            phase_data[ph]["y"].append(label)
            phase_data[ph]["base"].append(seg["start"])
            phase_data[ph]["width"].append(seg["duration"])
            phase_data[ph]["hover"].append(
                f"<b>{label}</b><br>Phase: {ph}<br>"
                f"Start: {seg['start']:.2f}h<br>"
                f"Duration: {seg['duration']:.2f}h<extra></extra>"
            )

    fig = go.Figure()
    shown_phases = set()
    for ph in phase_order:
        d = phase_data[ph]
        if not d["y"]:
            continue
        show_legend = ph not in shown_phases
        shown_phases.add(ph)
        fig.add_trace(go.Bar(
            name=ph,
            orientation="h",
            y=d["y"],
            x=d["width"],
            base=d["base"],
            marker=dict(
                color=phase_colors[ph],
                line=dict(width=0.5, color="rgba(0,0,0,0.05)"),
            ),
            hovertemplate=d["hover"],
            showlegend=show_legend,
        ))

    # Reference line at current time
    if current_t > 0:
        fig.add_vline(
            x=current_t,
            line_dash="dash",
            line_color="#1e293b",
            annotation_text=f"Now ({current_t:.2f}h)",
            annotation_position="top right",
            annotation_font_color="#1e293b",
        )

    fig.update_layout(
        barmode="overlay",
        title=dict(text="Simulation Timeline — System Phase History", font=dict(size=15)),
        xaxis=dict(
            title="Simulation Time (hours)",
            gridcolor="rgba(0,0,0,0.05)",
            zeroline=False,
            ticksuffix="h",
        ),
        yaxis=dict(
            autorange="reversed",
            gridcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(t=60, b=40, l=20, r=20),
        height=max(200, 60 + len(bar_traces) * 45),
    )
    return fig
