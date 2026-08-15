import plotly.graph_objects as go
import networkx as nx

from app.core.simulation_engine import SimulationEngine
from app.database.repositories import SystemRepository
from app.database.sqlite_manager import SQLiteManager

def generate_plotly_graph(engine: SimulationEngine, db: SQLiteManager) -> go.Figure:
    """
    Generates a Plotly network graph representing the dependency structure
    and current runtime state of the systems.
    """
    G = engine.dep_graph.graph
    
    # Use networkx layout
    # Spring layout works, but for hierarchical systems dot or kamada_kawai is better.
    pos = nx.spring_layout(G, seed=42)
    
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines'
    )

    node_x = []
    node_y = []
    node_colors = []
    node_texts = []
    
    sys_repo = SystemRepository(db)
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        # Determine state
        state = engine.system_states.get(node)
        avail = state.effective_availability if state else 1.0
        
        # Colors: Green=1.0, Yellow=0.1-0.99, Red=0.0
        if avail >= 1.0:
            color = 'green'
            status_text = "Healthy"
        elif avail <= 0.0:
            color = 'red'
            status_text = "Failed"
        else:
            color = 'orange'
            status_text = f"Degraded ({avail*100:.0f}%)"
            
        sys_obj = sys_repo.get(node)
        name = sys_obj.name if sys_obj else node
            
        node_colors.append(color)
        node_texts.append(f"{name}<br>State: {status_text}")

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        hovertext=node_texts,
        text=[sys_repo.get(n).name if sys_repo.get(n) else n for n in G.nodes()],
        textposition="bottom center",
        marker=dict(
            showscale=False,
            color=node_colors,
            size=30,
            line_width=2
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                title='<br>System Dependency Graph',
                titlefont_size=16,
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
             )
             
    return fig
