"""
Explainable resilience scoring engine.

Maintains a score ledger — every decision or event produces a ScoreEvent
explaining what changed and why. The final resilience score is the sum
of all deltas, making the scoring fully auditable and explainable.

Score categories (per spec §17):
    - Recovery Performance
    - Data Protection
    - Business Availability
    - Resource Efficiency
    - Cost Efficiency
"""

from app.models.simulation import ScoreEvent
from app.models.enums import ScoreCategory


# Starting score per category
_BASE_SCORE = 100.0

# Weights for final composite score (sum to 1.0)
CATEGORY_WEIGHTS = {
    ScoreCategory.RECOVERY_PERFORMANCE: 0.25,
    ScoreCategory.DATA_PROTECTION: 0.20,
    ScoreCategory.BUSINESS_AVAILABILITY: 0.25,
    ScoreCategory.RESOURCE_EFFICIENCY: 0.15,
    ScoreCategory.COST_EFFICIENCY: 0.15,
}


class ScoringEngine:
    """
    Tracks resilience score changes through an explainable ledger.

    Each action/decision produces a ScoreEvent with:
        - decision_id (optional)
        - category (which dimension is affected)
        - delta (positive or negative change)
        - reason (plain-English explanation)
        - event_time (simulation clock)

    The final composite score is a weighted sum of category scores,
    normalized to 0–100.
    """

    def __init__(self, run_id: str):
        self.run_id = run_id
        self._ledger: list[ScoreEvent] = []
        self._category_totals: dict[ScoreCategory, float] = {
            cat: _BASE_SCORE for cat in ScoreCategory
        }

    def record(
        self,
        category: ScoreCategory,
        delta: float,
        reason: str,
        event_time: float,
        decision_id: str | None = None,
    ) -> ScoreEvent:
        """
        Record a score change with explanation.

        Args:
            category: Which resilience dimension is affected
            delta: Positive (good) or negative (bad) score change
            reason: Plain-English explanation, e.g.
                    "RTO exceeded by 2h because backup was unavailable"
            event_time: Simulation clock time
            decision_id: Optional link to the decision that caused this

        Returns:
            The created ScoreEvent
        """
        event = ScoreEvent(
            run_id=self.run_id,
            decision_id=decision_id,
            category=category,
            delta=delta,
            reason=reason,
            event_time=event_time,
        )
        self._ledger.append(event)
        self._category_totals[category] += delta
        return event

    def get_category_score(self, category: ScoreCategory) -> float:
        """Get current score for a specific category."""
        return max(0.0, self._category_totals[category])

    def get_composite_score(self) -> float:
        """
        Compute weighted composite resilience score (0–100).

        Each category is clamped to [0, 100] before weighting.
        """
        total = 0.0
        for category, weight in CATEGORY_WEIGHTS.items():
            cat_score = max(0.0, min(100.0, self._category_totals[category]))
            total += cat_score * weight
        return round(total, 2)

    def get_category_scores(self) -> dict[str, float]:
        """Get all category scores as a dict (for radar chart)."""
        return {
            cat.value: max(0.0, min(100.0, self._category_totals[cat]))
            for cat in ScoreCategory
        }

    def get_ledger(self) -> list[ScoreEvent]:
        """Return the full score event ledger."""
        return list(self._ledger)

    def get_positive_events(self) -> list[ScoreEvent]:
        """Return events with positive deltas."""
        return [e for e in self._ledger if e.delta > 0]

    def get_negative_events(self) -> list[ScoreEvent]:
        """Return events with negative deltas."""
        return [e for e in self._ledger if e.delta < 0]

    def summarize(self) -> dict:
        """
        Summary for report generation.

        Returns dict with composite score, per-category scores,
        top positive/negative events, and total event count.
        """
        positive = self.get_positive_events()
        negative = self.get_negative_events()

        return {
            "composite_score": self.get_composite_score(),
            "category_scores": self.get_category_scores(),
            "total_events": len(self._ledger),
            "positive_count": len(positive),
            "negative_count": len(negative),
            "top_positive": sorted(positive, key=lambda e: e.delta, reverse=True)[:5],
            "top_negative": sorted(negative, key=lambda e: e.delta)[:5],
        }
