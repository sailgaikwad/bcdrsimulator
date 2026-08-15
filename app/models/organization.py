"""
Organization and business service domain models.

These represent the 'business layer' of the BC/DR simulator:
- Organization: the entity being simulated
- BusinessService: revenue-generating services with BIA parameters (RTO, RPO, MTPD)
"""

from pydantic import BaseModel, Field
from typing import Optional
import uuid


def _new_id() -> str:
    return str(uuid.uuid4())


class Organization(BaseModel):
    """
    Top-level entity representing the organization being simulated.
    All systems, services, and simulations belong to an organization.
    """
    id: str = Field(default_factory=_new_id)
    name: str
    industry: Optional[str] = None

    model_config = {"frozen": False}


class BusinessService(BaseModel):
    """
    A business-facing service with Business Impact Analysis (BIA) parameters.

    BIA parameters:
        criticality: 1–10 scale (10 = most critical)
        rto_hours: Recovery Time Objective — target time to restore service
        rpo_hours: Recovery Point Objective — acceptable data loss in hours
        mtpd_hours: Maximum Tolerable Period of Disruption — absolute max downtime
                    before business failure. Must be >= rto_hours.
        revenue_per_hour: Simulated revenue-loss rate during outage
        sla_penalty_per_hour: Simulated SLA penalty rate
        reputation_decay_rate: Reputation impact rate (0.0–1.0 scale per hour)
        notification_deadline_hours: Regulatory notification clock for data-compromise scenarios
    """
    id: str = Field(default_factory=_new_id)
    org_id: str
    name: str
    criticality: int = Field(default=5, ge=1, le=10)
    rto_hours: Optional[float] = Field(default=4.0, ge=0.0)
    rpo_hours: Optional[float] = Field(default=1.0, ge=0.0)
    mtpd_hours: Optional[float] = Field(default=24.0, ge=0.0)
    revenue_per_hour: Optional[float] = Field(default=0.0, ge=0.0)
    sla_penalty_per_hour: Optional[float] = Field(default=0.0, ge=0.0)
    reputation_decay_rate: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    notification_deadline_hours: Optional[float] = None

    model_config = {"frozen": False}
