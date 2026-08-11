from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


RiskLevel = Literal["insufficient_data", "green", "yellow", "red"]
EscalationAction = Literal["continue_monitoring", "schedule_medical_review", "seek_timely_medical_evaluation", "urgent_escalation"]


class HealthSettingUpdate(BaseModel):
    western_prevention_enabled: bool | None = None
    tcm_health_enabled: bool | None = None
    tcm_consent_confirmed: bool = False
    tcm_consent_version: str | None = None
    tcm_depth: Literal["basic", "deep"] | None = None


class PreventionItemCreate(BaseModel):
    member_id: int
    title: str
    category: str
    reason: str
    due_date: date | None = None
    status: Literal["not_due", "due_soon", "due", "completed", "dismissed", "unknown"] = "unknown"
    source_type: str
    source_reference: str | None = None
    rule_id: str | None = None


class RecomputeRequest(BaseModel):
    member_id: int
    trigger_type: str = "manual"
    trigger_source_id: int | None = None


class EvidenceRead(BaseModel):
    source_type: str
    source_id: str
    recorded_at: datetime | None
    original_text: str | None
    summary: str
    confirmed_by_user: bool
    confidence: str
