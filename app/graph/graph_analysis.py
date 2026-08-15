"""
Graph analysis for SPOF detection, centrality metrics, and
plain-English vulnerability explanations.

Uses NetworkX algorithms: articulation points, centrality measures,
connected components, and shortest paths to identify infrastructure
weaknesses before a crisis begins.
"""

import networkx as nx
from dataclasses import dataclass, field
from typing import Optional

from app.graph.dependency_graph import DependencyGraph


@dataclass
class SPOFResult:
    """A single-point-of-failure finding with explanation."""
    system_id: str
    system_name: str
    reason: str
    affected_downstream: list[str]   # names of affected systems
    severity: str                    # LOW, MEDIUM, HIGH, CRITICAL


@dataclass
class GraphMetrics:
    """Centrality and structural metrics for the infrastructure graph."""
    degree_centrality: dict[str, float] = field(default_factory=dict)
    betweenness_centrality: dict[str, float] = field(default_factory=dict)
    pagerank: dict[str, float] = field(default_factory=dict)
    in_degree: dict[str, int] = field(default_factory=dict)
    out_degree: dict[str, int] = field(default_factory=dict)
    articulation_points: list[str] = field(default_factory=list)
    connected_components: int = 0
    is_dag: bool = True


class GraphAnalysis:
    """
    Performs structural analysis on the infrastructure dependency graph.

    Provides:
    - Centrality metrics (degree, betweenness, PageRank)
    - Articulation point detection (SPOF)
    - Connected component analysis
    - Plain-English vulnerability explanations
    """

    def __init__(self, dep_graph: DependencyGraph):
        self._dep_graph = dep_graph
        self._graph = dep_graph.graph

    def compute_metrics(self) -> GraphMetrics:
        """Compute all centrality and structural metrics."""
        metrics = GraphMetrics()

        if self._graph.number_of_nodes() == 0:
            return metrics

        # Degree centrality
        metrics.degree_centrality = nx.degree_centrality(self._graph)

        # Betweenness centrality — identifies bottleneck nodes
        metrics.betweenness_centrality = nx.betweenness_centrality(self._graph)

        # PageRank — importance based on incoming dependency links
        try:
            metrics.pagerank = nx.pagerank(self._graph)
        except nx.PowerIterationFailedConvergence:
            metrics.pagerank = {n: 1.0 / self._graph.number_of_nodes()
                                for n in self._graph.nodes}

        # Degree counts
        metrics.in_degree = dict(self._graph.in_degree())
        metrics.out_degree = dict(self._graph.out_degree())

        # Articulation points — on undirected version
        # These are nodes whose removal disconnects the graph
        undirected = self._graph.to_undirected()
        metrics.articulation_points = list(nx.articulation_points(undirected))

        # Connected components (undirected)
        metrics.connected_components = nx.number_connected_components(undirected)

        # DAG check
        metrics.is_dag = nx.is_directed_acyclic_graph(self._graph)

        return metrics

    def find_spofs(self) -> list[SPOFResult]:
        """
        Identify single points of failure using articulation points
        and dependency fan-out analysis.

        Returns plain-English explanations for each vulnerability.
        """
        results = []
        metrics = self.compute_metrics()

        # 1. Articulation points — removing these disconnects the graph
        for ap_id in metrics.articulation_points:
            node_data = self._dep_graph.get_node_data(ap_id)
            name = node_data.get("name", ap_id) if node_data else ap_id

            downstream = self._dep_graph.get_all_downstream(ap_id)
            downstream_names = []
            for ds_id in downstream:
                ds_data = self._dep_graph.get_node_data(ds_id)
                downstream_names.append(
                    ds_data.get("name", ds_id) if ds_data else ds_id
                )

            severity = self._classify_severity(len(downstream), metrics, ap_id)

            reason = self._generate_explanation(name, downstream_names, metrics, ap_id)

            results.append(SPOFResult(
                system_id=ap_id,
                system_name=name,
                reason=reason,
                affected_downstream=downstream_names,
                severity=severity,
            ))

        # 2. High fan-out nodes (not articulation points but risky)
        for node_id in self._graph.nodes:
            if node_id in metrics.articulation_points:
                continue

            out_deg = metrics.out_degree.get(node_id, 0)
            betweenness = metrics.betweenness_centrality.get(node_id, 0.0)

            if out_deg >= 3 or betweenness > 0.3:
                node_data = self._dep_graph.get_node_data(node_id)
                name = node_data.get("name", node_id) if node_data else node_id

                downstream = self._dep_graph.get_all_downstream(node_id)
                downstream_names = []
                for ds_id in downstream:
                    ds_data = self._dep_graph.get_node_data(ds_id)
                    downstream_names.append(
                        ds_data.get("name", ds_id) if ds_data else ds_id
                    )

                severity = "MEDIUM" if out_deg >= 3 else "LOW"

                reason = (
                    f"{name} has high dependency fan-out ({out_deg} direct dependents) "
                    f"and betweenness centrality of {betweenness:.2f}. "
                    f"If it fails, {len(downstream_names)} system(s) could be affected: "
                    f"{', '.join(downstream_names[:5])}"
                    + (f" and {len(downstream_names) - 5} more" if len(downstream_names) > 5 else "")
                    + "."
                )

                results.append(SPOFResult(
                    system_id=node_id,
                    system_name=name,
                    reason=reason,
                    affected_downstream=downstream_names,
                    severity=severity,
                ))

        # Sort by severity (CRITICAL first)
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        results.sort(key=lambda r: severity_order.get(r.severity, 99))

        return results

    def find_shortest_paths(self, source_id: str) -> dict[str, list[str]]:
        """Find shortest paths from a source to all reachable nodes."""
        if source_id not in self._graph:
            return {}
        paths = {}
        for target in self._graph.nodes:
            if target == source_id:
                continue
            try:
                path = nx.shortest_path(self._graph, source_id, target)
                paths[target] = path
            except nx.NetworkXNoPath:
                continue
        return paths

    def get_minimum_vertex_cuts(self, source_id: str, target_id: str) -> Optional[set[str]]:
        """
        Find minimum vertex cut between source and target.
        Returns the smallest set of nodes whose removal disconnects them.
        """
        try:
            return nx.minimum_node_cut(self._graph, source_id, target_id)
        except (nx.NetworkXError, nx.NetworkXUnfeasible):
            return None

    def _classify_severity(self, downstream_count: int, metrics: GraphMetrics, node_id: str) -> str:
        """Classify SPOF severity based on downstream impact and centrality."""
        betweenness = metrics.betweenness_centrality.get(node_id, 0.0)

        if downstream_count >= 5 or betweenness > 0.5:
            return "CRITICAL"
        elif downstream_count >= 3 or betweenness > 0.3:
            return "HIGH"
        elif downstream_count >= 1:
            return "MEDIUM"
        else:
            return "LOW"

    def _generate_explanation(
        self, name: str, downstream_names: list[str],
        metrics: GraphMetrics, node_id: str
    ) -> str:
        """Generate a plain-English explanation of why a node is a SPOF."""
        count = len(downstream_names)

        if count == 0:
            return (
                f"{name} is an articulation point in the infrastructure graph. "
                f"Its removal would disconnect part of the topology."
            )

        affected_str = ", ".join(downstream_names[:5])
        if count > 5:
            affected_str += f" and {count - 5} more"

        betweenness = metrics.betweenness_centrality.get(node_id, 0.0)

        explanation = (
            f"{name} is a single point of failure because "
            f"{count} system(s) have no alternate path if it becomes unavailable"
            f" ({affected_str}). "
        )

        if betweenness > 0.3:
            explanation += (
                f"It also has high betweenness centrality ({betweenness:.2f}), "
                f"meaning it sits on many critical paths between systems."
            )

        return explanation
