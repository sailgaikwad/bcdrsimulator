"""
Discrete-event simulation priority queue.

Uses Python's heapq to maintain events ordered by (time, priority, sequence).
The sequence counter provides stable FIFO ordering for events at the same
time and priority, avoiding comparison issues with payload objects.
"""

import heapq
from dataclasses import dataclass, field
from typing import Optional

from app.models.simulation import SimulationEvent


class EventQueue:
    """
    A priority queue for discrete-event simulation.

    Events are ordered by:
        1. time (earliest first)
        2. priority (lowest number = highest priority)
        3. insertion order (FIFO for ties)

    This ensures deterministic, reproducible event processing.
    """

    def __init__(self):
        self._heap: list[tuple[float, int, int, SimulationEvent]] = []
        self._counter: int = 0  # Tie-breaking sequence number

    def push(self, event: SimulationEvent) -> None:
        """Add an event to the queue."""
        entry = (event.time, event.priority, self._counter, event)
        heapq.heappush(self._heap, entry)
        self._counter += 1

    def pop(self) -> Optional[SimulationEvent]:
        """Remove and return the next event (earliest time, highest priority)."""
        if not self._heap:
            return None
        _, _, _, event = heapq.heappop(self._heap)
        return event

    def peek(self) -> Optional[SimulationEvent]:
        """Look at the next event without removing it."""
        if not self._heap:
            return None
        return self._heap[0][3]

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def __len__(self) -> int:
        return len(self._heap)

    def clear(self) -> None:
        """Remove all events."""
        self._heap.clear()
        self._counter = 0

    def drain(self) -> list[SimulationEvent]:
        """Remove and return all events in order. Useful for debugging."""
        events = []
        while not self.is_empty():
            events.append(self.pop())
        return events
