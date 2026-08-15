"""
Dependency graph built on NetworkX DiGraph.

Wraps NetworkX to provide a domain-specific API for the BCDR simulator's
infrastructure topology. The graph direction is source → target,
meaning 'target depends on source'.
"""

import networkx as nx
from typing import Optional

from app.models.system import System
from app.models.dependency import Dependency
from app.models.enums import DependencyType


class DependencyGraph:
    """
    A directed infrastructure dependency graph.

    Nodes are systems (keyed by system.id).
    Edges are dependencies with type (hard/soft) and weight attributes.

    Convention: edge from A → B means B depends on A.
                If A fails, B is affected.
    """

    def __init__(self):
        self._graph = nx.DiGraph()

    @property
    def graph(self) -> nx.DiGraph:
        """Access the underlying NetworkX DiGraph for advanced analysis."""
        return self._graph

    def add_system(self, system: System) -> None:
        """Add a system as a node in the graph."""
        self._graph.add_node(
            system.id,
            name=system.name,
            system_type=system.system_type.value,
            tier=system.tier.value,
            base_health=system.base_health,
            recovery_priority=system.recovery_priority,
        )

    def remove_system(self, system_id: str) -> None:
        """Remove a system and all its edges from the graph."""
        if system_id in self._graph:
            self._graph.remove_node(system_id)

    def add_dependency(self, dep: Dependency) -> None:
        """
        Add a dependency edge: source → target.
        Target depends on source.
        """
        self._graph.add_edge(
            dep.source_id,
            dep.target_id,
            dep_id=dep.id,
            dep_type=dep.dep_type.value,
            weight=dep.weight,
            description=dep.description,
        )

    def remove_dependency(self, source_id: str, target_id: str) -> None:
        """Remove a dependency edge."""
        if self._graph.has_edge(source_id, target_id):
            self._graph.remove_edge(source_id, target_id)

    def get_upstream(self, system_id: str) -> list[tuple[str, dict]]:
        """
        Get systems that this system depends on (predecessors).
        Returns list of (upstream_id, edge_data) tuples.
        """
        if system_id not in self._graph:
            return []
        return [
            (pred, self._graph.edges[pred, system_id])
            for pred in self._graph.predecessors(system_id)
        ]

    def get_downstream(self, system_id: str) -> list[tuple[str, dict]]:
        """
        Get systems that depend on this system (successors).
        Returns list of (downstream_id, edge_data) tuples.
        """
        if system_id not in self._graph:
            return []
        return [
            (succ, self._graph.edges[system_id, succ])
            for succ in self._graph.successors(system_id)
        ]

    def get_all_downstream(self, system_id: str) -> set[str]:
        """
        Get ALL systems transitively downstream (affected if this system fails).
        Uses BFS/DFS through the graph.
        """
        if system_id not in self._graph:
            return set()
        return set(nx.descendants(self._graph, system_id))

    def get_node_data(self, system_id: str) -> Optional[dict]:
        """Get node attributes for a system."""
        if system_id not in self._graph:
            return None
        return dict(self._graph.nodes[system_id])

    def get_topological_order(self) -> list[str]:
        """
        Return systems in topological order (dependencies first).
        Useful for propagation — process upstream systems before downstream.

        Returns empty list if graph has cycles.
        """
        try:
            return list(nx.topological_sort(self._graph))
        except nx.NetworkXUnfeasible:
            # Graph has cycles — fall back to arbitrary order
            return list(self._graph.nodes)

    def has_system(self, system_id: str) -> bool:
        return system_id in self._graph

    def system_count(self) -> int:
        return self._graph.number_of_nodes()

    def dependency_count(self) -> int:
        return self._graph.number_of_edges()

    def get_all_system_ids(self) -> list[str]:
        return list(self._graph.nodes)

    @classmethod
    def build(cls, systems: list[System], dependencies: list[Dependency]) -> "DependencyGraph":
        """
        Factory method: build a complete graph from lists of systems and dependencies.
        """
        graph = cls()
        for system in systems:
            graph.add_system(system)
        for dep in dependencies:
            graph.add_dependency(dep)
        return graph
