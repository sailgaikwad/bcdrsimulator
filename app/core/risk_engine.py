"""
Risk assessment engine implementing P × I × E model.

Risk = Probability × Impact × Exposure

Provides both per-system and aggregate risk calculations,
with risk level classification (LOW/MEDIUM/HIGH/CRITICAL).
"""

from app.models.simulation import RiskAssessment
from app.models.enums import RiskLevel
from app.models.system import SystemState
from app.models.organization import BusinessService
from app.graph.dependency_graph import DependencyGraph


class RiskEngine:
    """
    Calculates risk scores using the P × I × E model.

    Factors:
        Probability: Base scenario probability × system vulnerability
        Impact: BIA criticality × revenue weight × SLA weight
        Exposure: Duration of disruption / MTPD × dependency fan-out
    """

    def assess_system(
        self,
        run_id: str,
        system_state: SystemState,
        scenario_severity: float,
        bia_criticality: float,
        mtpd_hours: float,
        current_time: float,
        dep_graph: DependencyGraph,
    ) -> RiskAssessment:
        """
        Assess risk for a single system at a point in time.

        Args:
            system_state: Current runtime state of the system
            scenario_severity: Disaster severity (0.0–1.0)
            bia_criticality: Normalized BIA criticality (0.0–1.0)
            mtpd_hours: Maximum tolerable disruption period
            current_time: Current simulation clock time
            dep_graph: Dependency graph for fan-out calculation
        """
        # Probability: scenario severity × how degraded the system is
        probability = scenario_severity * (1.0 - system_state.effective_availability)

        # Impact: BIA criticality (already 0.0–1.0 normalized)
        impact = bia_criticality

        # Exposure: time-based + structural
        if system_state.failed_at is not None and mtpd_hours > 0:
            downtime = current_time - system_state.failed_at
            time_exposure = min(1.0, downtime / mtpd_hours)
        else:
            time_exposure = 0.0

        # Structural exposure: how many downstream systems are affected
        downstream = dep_graph.get_all_downstream(system_state.system_id)
        total_nodes = dep_graph.system_count()
        structural_exposure = len(downstream) / max(1, total_nodes)

        exposure = min(1.0, 0.6 * time_exposure + 0.4 * structural_exposure)

        assessment = RiskAssessment(
            run_id=run_id,
            system_id=system_state.system_id,
            assessment_time=current_time,
            probability=round(probability, 4),
            impact=round(impact, 4),
            exposure=round(exposure, 4),
        )
        assessment.compute()
        return assessment

    def assess_aggregate(
        self,
        run_id: str,
        system_assessments: list[RiskAssessment],
        current_time: float,
    ) -> RiskAssessment:
        """
        Compute aggregate risk across all systems.

        Uses the maximum risk score (worst-case) as the aggregate,
        with averaged probability and exposure for context.
        """
        if not system_assessments:
            return RiskAssessment(
                run_id=run_id,
                assessment_time=current_time,
                probability=0.0, impact=0.0, exposure=0.0,
            )

        max_risk = max(system_assessments, key=lambda a: a.risk_score or 0.0)

        avg_prob = sum(a.probability for a in system_assessments) / len(system_assessments)
        avg_impact = sum(a.impact for a in system_assessments) / len(system_assessments)
        avg_exposure = sum(a.exposure for a in system_assessments) / len(system_assessments)

        aggregate = RiskAssessment(
            run_id=run_id,
            assessment_time=current_time,
            probability=round(avg_prob, 4),
            impact=round(avg_impact, 4),
            exposure=round(avg_exposure, 4),
            notes=f"Aggregate of {len(system_assessments)} systems. "
                  f"Worst: {max_risk.system_id} (score={max_risk.risk_score:.3f})",
        )
        aggregate.compute()
        return aggregate
