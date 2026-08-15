"""
Tests for the dependency graph and graph analysis engine.

Validates:
- Graph construction from systems and dependencies
- Upstream/downstream queries
- Topological ordering
- Articulation point detection
- SPOF finding with plain-English explanations
- Centrality metrics
- Transitive dependency discovery
"""

import pytest
from app.graph.dependency_graph import DependencyGraph
from app.graph.graph_analysis import GraphAnalysis, SPOFResult
from app.models.system import System
from app.models.dependency import Dependency
from app.models.enums import SystemType, SystemTier, DependencyType


def _make_system(sid: str, name: str, stype: SystemType = SystemType.SERVER) -> System:
    return System(id=sid, org_id="org-1", name=name, system_type=stype)


def _make_dep(src: str, tgt: str, dep_type=DependencyType.HARD, weight=1.0) -> Dependency:
    return Dependency(
        org_id="org-1", source_id=src, target_id=tgt,
        dep_type=dep_type, weight=weight,
    )


class TestDependencyGraph:
    """Tests for the DependencyGraph wrapper."""

    def test_empty_graph(self):
        g = DependencyGraph()
        assert g.system_count() == 0
        assert g.dependency_count() == 0

    def test_add_systems(self):
        g = DependencyGraph()
        g.add_system(_make_system("s1", "Server A"))
        g.add_system(_make_system("s2", "Server B"))
        assert g.system_count() == 2

    def test_add_dependency(self):
        g = DependencyGraph()
        g.add_system(_make_system("s1", "Server A"))
        g.add_system(_make_system("s2", "Server B"))
        g.add_dependency(_make_dep("s1", "s2"))
        assert g.dependency_count() == 1

    def test_upstream_downstream(self):
        g = DependencyGraph()
        g.add_system(_make_system("s1", "Server A"))
        g.add_system(_make_system("s2", "Server B"))
        g.add_dependency(_make_dep("s1", "s2"))

        # s2 depends on s1
        upstream = g.get_upstream("s2")
        assert len(upstream) == 1
        assert upstream[0][0] == "s1"

        # s1 has s2 as downstream
        downstream = g.get_downstream("s1")
        assert len(downstream) == 1
        assert downstream[0][0] == "s2"

    def test_transitive_downstream(self):
        g = DependencyGraph()
        for i in range(1, 5):
            g.add_system(_make_system(f"s{i}", f"System {i}"))
        g.add_dependency(_make_dep("s1", "s2"))
        g.add_dependency(_make_dep("s2", "s3"))
        g.add_dependency(_make_dep("s3", "s4"))

        # s1 failure should transitively affect s2, s3, s4
        downstream = g.get_all_downstream("s1")
        assert downstream == {"s2", "s3", "s4"}

    def test_topological_order(self):
        g = DependencyGraph()
        g.add_system(_make_system("gateway", "Gateway", SystemType.GATEWAY))
        g.add_system(_make_system("fw", "Firewall", SystemType.FIREWALL))
        g.add_system(_make_system("app", "App Server", SystemType.APPLICATION))
        g.add_system(_make_system("db", "Database", SystemType.DATABASE))

        g.add_dependency(_make_dep("gateway", "fw"))
        g.add_dependency(_make_dep("fw", "app"))
        g.add_dependency(_make_dep("app", "db"))

        order = g.get_topological_order()
        assert order.index("gateway") < order.index("fw")
        assert order.index("fw") < order.index("app")
        assert order.index("app") < order.index("db")

    def test_build_factory(self):
        systems = [
            _make_system("s1", "A"),
            _make_system("s2", "B"),
            _make_system("s3", "C"),
        ]
        deps = [_make_dep("s1", "s2"), _make_dep("s2", "s3")]
        g = DependencyGraph.build(systems, deps)
        assert g.system_count() == 3
        assert g.dependency_count() == 2

    def test_remove_system(self):
        g = DependencyGraph()
        g.add_system(_make_system("s1", "A"))
        g.add_system(_make_system("s2", "B"))
        g.add_dependency(_make_dep("s1", "s2"))
        g.remove_system("s1")
        assert g.system_count() == 1
        assert g.dependency_count() == 0

    def test_node_data(self):
        g = DependencyGraph()
        g.add_system(_make_system("s1", "Gateway", SystemType.GATEWAY))
        data = g.get_node_data("s1")
        assert data is not None
        assert data["name"] == "Gateway"
        assert data["system_type"] == "gateway"

    def test_nonexistent_node(self):
        g = DependencyGraph()
        assert g.get_node_data("nope") is None
        assert g.get_upstream("nope") == []
        assert g.get_downstream("nope") == []
        assert g.get_all_downstream("nope") == set()


class TestGraphAnalysis:
    """Tests for SPOF detection and centrality analysis."""

    def _build_linear_graph(self) -> DependencyGraph:
        """Gateway → Firewall → App → DB (linear chain)"""
        g = DependencyGraph()
        g.add_system(_make_system("gw", "Internet Gateway", SystemType.GATEWAY))
        g.add_system(_make_system("fw", "Firewall", SystemType.FIREWALL))
        g.add_system(_make_system("app", "Application Cluster", SystemType.APPLICATION))
        g.add_system(_make_system("db", "Primary Database", SystemType.DATABASE))
        g.add_dependency(_make_dep("gw", "fw"))
        g.add_dependency(_make_dep("fw", "app"))
        g.add_dependency(_make_dep("app", "db"))
        return g

    def _build_branching_graph(self) -> DependencyGraph:
        """
        Gateway → Firewall → App
                           → Cache
        Firewall → DB (separate branch)
        """
        g = DependencyGraph()
        g.add_system(_make_system("gw", "Gateway", SystemType.GATEWAY))
        g.add_system(_make_system("fw", "Firewall", SystemType.FIREWALL))
        g.add_system(_make_system("app", "App Server", SystemType.APPLICATION))
        g.add_system(_make_system("cache", "Cache", SystemType.CACHE))
        g.add_system(_make_system("db", "Database", SystemType.DATABASE))
        g.add_dependency(_make_dep("gw", "fw"))
        g.add_dependency(_make_dep("fw", "app"))
        g.add_dependency(_make_dep("fw", "cache", DependencyType.SOFT, 0.5))
        g.add_dependency(_make_dep("fw", "db"))
        return g

    def test_metrics_empty_graph(self):
        g = DependencyGraph()
        analysis = GraphAnalysis(g)
        metrics = analysis.compute_metrics()
        assert metrics.connected_components == 0

    def test_metrics_linear(self):
        g = self._build_linear_graph()
        analysis = GraphAnalysis(g)
        metrics = analysis.compute_metrics()

        assert len(metrics.degree_centrality) == 4
        assert len(metrics.betweenness_centrality) == 4
        assert metrics.is_dag
        # Firewall and App should be articulation points in undirected version
        assert len(metrics.articulation_points) >= 1

    def test_spof_detection(self):
        g = self._build_branching_graph()
        analysis = GraphAnalysis(g)
        spofs = analysis.find_spofs()

        # Firewall should be detected — it's the bottleneck
        spof_names = [s.system_name for s in spofs]
        assert "Firewall" in spof_names

    def test_spof_has_explanation(self):
        g = self._build_branching_graph()
        analysis = GraphAnalysis(g)
        spofs = analysis.find_spofs()

        for spof in spofs:
            assert spof.reason  # must have a plain-English explanation
            assert spof.severity in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    def test_shortest_paths(self):
        g = self._build_linear_graph()
        analysis = GraphAnalysis(g)
        paths = analysis.find_shortest_paths("gw")

        assert "db" in paths
        assert paths["db"] == ["gw", "fw", "app", "db"]

    def test_pagerank(self):
        g = self._build_branching_graph()
        analysis = GraphAnalysis(g)
        metrics = analysis.compute_metrics()

        # All nodes should have a PageRank value
        assert len(metrics.pagerank) == 5
        # PageRank values should sum to ~1.0
        total = sum(metrics.pagerank.values())
        assert abs(total - 1.0) < 0.01
