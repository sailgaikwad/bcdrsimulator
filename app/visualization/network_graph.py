import plotly.graph_objects as go
import networkx as nx

from app.core.simulation_engine import SimulationEngine
from app.database.repositories import SystemRepository
from app.database.sqlite_manager import SQLiteManager
from app.models.enums import DependencyType, SystemType

def generate_plotly_graph(engine: SimulationEngine, db: SQLiteManager) -> go.Figure:
    """
    Generates a Plotly network graph representing the dependency structure
    and current runtime state of the systems.
    """
    G = engine.dep_graph.graph
    sys_repo = SystemRepository(db)
    
    # Assign subsets based on typical architecture tiers for multipartite layout
    tier_map = {
        SystemType.GATEWAY: 0,
        SystemType.NETWORK: 1,
        SystemType.FIREWALL: 2,
        SystemType.LOAD_BALANCER: 3,
        SystemType.APPLICATION: 4,
        SystemType.CACHE: 5,
        SystemType.DATABASE: 6,
        SystemType.STORAGE: 7,
        SystemType.SERVER: 7,
        SystemType.BACKUP: 8,
    }
    
    for node in G.nodes():
        sys_obj = sys_repo.get(node)
        G.nodes[node]['subset'] = tier_map.get(sys_obj.system_type, 4) if sys_obj else 4
        
    pos = nx.multipartite_layout(G, scale=1)
    
    edge_x = []
    edge_y = []
    edge_dash_x = []
    edge_dash_y = []
    edge_disrupted_x = []
    edge_disrupted_y = []
    
    for edge in G.edges(data=True):
        src = edge[0]
        x0, y0 = pos[src]
        x1, y1 = pos[edge[1]]
        
        src_state = engine.system_states.get(src)
        src_avail = src_state.effective_availability if src_state else 1.0
        
        dep_type = edge[2].get('dep_type')
        if src_avail < 1.0:
            edge_disrupted_x.extend([x0, x1, None])
            edge_disrupted_y.extend([y0, y1, None])
        elif dep_type == DependencyType.DATA_SYNC.value or dep_type == DependencyType.DATA_SYNC:
            edge_dash_x.extend([x0, x1, None])
            edge_dash_y.extend([y0, y1, None])
        else:
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1.5, color='#888'),
        hoverinfo='none',
        mode='lines'
    )
    
    edge_dash_trace = go.Scatter(
        x=edge_dash_x, y=edge_dash_y,
        line=dict(width=1.5, color='#aaa', dash='dash'),
        hoverinfo='none',
        mode='lines'
    )

    edge_disrupted_trace = go.Scatter(
        x=edge_disrupted_x, y=edge_disrupted_y,
        line=dict(width=2.0, color='red', dash='dot'),
        hoverinfo='none',
        mode='lines'
    )

    node_x = []
    node_y = []
    node_colors = []
    node_texts = []
    node_display_texts = []
    

    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        # Determine state
        state = engine.system_states.get(node)
        avail = state.effective_availability if state else 1.0
        is_recovering = engine.recovery.is_system_recovering(node)
        
        # Colors: Blue=Recovering, Green=1.0, Yellow=0.1-0.99, Red=0.0
        if is_recovering:
            color = 'blue'
            status_text = "Recovering"
        elif avail >= 1.0:
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
        node_display_texts.append(f"{name}<br><span style='font-size:10px'>{avail*100:.0f}%</span>")

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        hovertext=node_texts,
        text=node_display_texts,
        textposition="bottom center",
        marker=dict(
            showscale=False,
            color=node_colors,
            size=30,
            line_width=2
        )
    )

    fig = go.Figure(data=[edge_trace, edge_dash_trace, edge_disrupted_trace, node_trace],
             layout=go.Layout(
                title=dict(text='<br>System Dependency Graph', font=dict(size=16)),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                annotations=[dict(
                    x=0.0,
                    y=1.0,
                    xref='paper',
                    yref='paper',
                    text='<b>Legend</b><br>🟢 Healthy (100%)<br>🔵 Recovering<br>🟠 Degraded<br>🔴 Failed (0%)<br>--- Hard Edge<br>- - Sync Edge<br>··· Disrupted Edge',
                    showarrow=False,
                    align='left',
                    bgcolor='rgba(255,255,255,0.8)',
                    bordercolor='black',
                    borderwidth=1
                )]
             )
    )
             
    return fig
