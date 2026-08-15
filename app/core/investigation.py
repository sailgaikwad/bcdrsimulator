"""
Investigation engine for the uncertainty mechanic.

Manages hidden facts (unknown to the user) and the investigation
trade-off: spending time investigating reveals information but
consumes time that could be used for recovery.

Per spec §14:
    "Investigate longer → more information → less uncertainty → less time for recovery"
"""

import random
from typing import Optional

from app.models.simulation import HiddenFact, SimulationEvent
from app.models.enums import EventType


class InvestigationEngine:
    """
    Manages hidden simulation facts and investigation actions.

    Hidden facts have:
        - true_value: the actual value (hidden from user)
        - revealed_low / revealed_high: the range shown to the user
        - confidence: how certain the user is (0.0–1.0)

    Investigation actions:
        - Cost time (configurable)
        - Narrow the revealed range toward the truth
        - Increase confidence
        - Create a genuine strategic trade-off
    """

    # Default investigation durations (hours)
    QUICK_INVESTIGATION_HOURS = 0.5
    STANDARD_INVESTIGATION_HOURS = 1.0
    THOROUGH_INVESTIGATION_HOURS = 2.0

    # Accuracy gained per investigation type
    QUICK_ACCURACY = 0.3
    STANDARD_ACCURACY = 0.5
    THOROUGH_ACCURACY = 0.8

    def __init__(self, run_id: str, rng: random.Random):
        self.run_id = run_id
        self._rng = rng
        self._facts: dict[str, HiddenFact] = {}

    def register_fact(
        self,
        fact_key: str,
        true_value: float,
        initial_low: float = 0.0,
        initial_high: float = 1.0,
    ) -> HiddenFact:
        """
        Register a hidden fact for this simulation run.

        The user initially sees only the range [initial_low, initial_high]
        and has zero confidence.
        """
        fact = HiddenFact(
            run_id=self.run_id,
            fact_key=fact_key,
            true_value=true_value,
            revealed_low=initial_low,
            revealed_high=initial_high,
            confidence=0.0,
            investigated=False,
        )
        self._facts[fact_key] = fact
        return fact

    def get_fact(self, fact_key: str) -> Optional[HiddenFact]:
        """Get a hidden fact by key."""
        return self._facts.get(fact_key)

    def get_all_facts(self) -> list[HiddenFact]:
        """Get all hidden facts."""
        return list(self._facts.values())

    def get_user_view(self, fact_key: str) -> Optional[dict]:
        """
        Get what the user can see about a fact (not the true value).

        Returns:
            {
                "fact_key": ...,
                "range": [low, high],
                "confidence": ...,
                "investigated": bool,
                "estimate": midpoint of range,
            }
        """
        fact = self._facts.get(fact_key)
        if fact is None:
            return None

        low = fact.revealed_low if fact.revealed_low is not None else 0.0
        high = fact.revealed_high if fact.revealed_high is not None else 1.0

        return {
            "fact_key": fact.fact_key,
            "range": [low, high],
            "confidence": fact.confidence,
            "investigated": fact.investigated,
            "estimate": (low + high) / 2.0,
        }

    def investigate(
        self,
        fact_key: str,
        investigation_type: str = "standard",
    ) -> tuple[Optional[HiddenFact], float]:
        """
        Perform an investigation on a hidden fact.

        Args:
            fact_key: Which fact to investigate
            investigation_type: "quick", "standard", or "thorough"

        Returns:
            (updated_fact, time_cost_hours)
            Returns (None, 0.0) if fact not found.
        """
        fact = self._facts.get(fact_key)
        if fact is None:
            return None, 0.0

        # Determine accuracy and time cost
        if investigation_type == "quick":
            accuracy = self.QUICK_ACCURACY
            time_cost = self.QUICK_INVESTIGATION_HOURS
        elif investigation_type == "thorough":
            accuracy = self.THOROUGH_ACCURACY
            time_cost = self.THOROUGH_INVESTIGATION_HOURS
        else:
            accuracy = self.STANDARD_ACCURACY
            time_cost = self.STANDARD_INVESTIGATION_HOURS

        # Add slight randomness to accuracy (±10%)
        noise = self._rng.uniform(-0.1, 0.1)
        accuracy = max(0.1, min(1.0, accuracy + noise))

        # Narrow the range
        fact.reveal_range(accuracy)

        return fact, time_cost

    def create_investigation_event(
        self,
        fact_key: str,
        investigation_type: str,
        current_time: float,
    ) -> Optional[SimulationEvent]:
        """
        Create a simulation event for an investigation action.

        Returns the INVESTIGATION_COMPLETE event to be scheduled,
        or None if the fact doesn't exist.
        """
        fact = self._facts.get(fact_key)
        if fact is None:
            return None

        # Determine time cost
        if investigation_type == "quick":
            time_cost = self.QUICK_INVESTIGATION_HOURS
        elif investigation_type == "thorough":
            time_cost = self.THOROUGH_INVESTIGATION_HOURS
        else:
            time_cost = self.STANDARD_INVESTIGATION_HOURS

        return SimulationEvent(
            run_id=self.run_id,
            event_type=EventType.INVESTIGATION_COMPLETE,
            time=current_time + time_cost,
            priority=4,
            description=f"Investigation of '{fact_key}' ({investigation_type}) completes",
            payload={
                "fact_key": fact_key,
                "investigation_type": investigation_type,
                "time_cost": time_cost,
            },
        )
