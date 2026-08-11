from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.db.session import Base


def now() -> datetime:
    return datetime.now().replace(microsecond=0)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class FamilyMember(Base, TimestampMixin):
    __tablename__ = "family_members"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    nickname: Mapped[str | None] = mapped_column(String(80), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True)
    relationship: Mapped[str | None] = mapped_column(String(50), nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferred_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile: Mapped[HealthProfile | None] = orm_relationship(back_populates="member", uselist=False)


class HealthProfile(Base, TimestampMixin):
    __tablename__ = "health_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("family_members.id"), unique=True)
    known_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    allergies: Mapped[str | None] = mapped_column(Text, nullable=True)
    past_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    family_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    medications: Mapped[str | None] = mapped_column(Text, nullable=True)
    height: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    smoking_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    drinking_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    doctor_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_version: Mapped[str | None] = mapped_column(String(30), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    profile_data: Mapped[str] = mapped_column(Text, default="{}")
    raw_profile_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    member: Mapped[FamilyMember] = orm_relationship(back_populates="profile")


class HealthLog(Base):
    __tablename__ = "health_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("family_members.id"), index=True)
    log_type: Mapped[str] = mapped_column(String(40), index=True)
    raw_text: Mapped[str] = mapped_column(Text)
    structured_data: Mapped[str] = mapped_column(Text, default="{}")
    source: Mapped[str] = mapped_column(String(40), default="user_reported")
    source_key: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    possible_emergency: Mapped[bool] = mapped_column(Boolean, default=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class MedicationCourse(Base, TimestampMixin):
    __tablename__ = "medication_courses"
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("family_members.id"), index=True)
    course_number: Mapped[int] = mapped_column(Integer, index=True)
    prescription_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    hospital: Mapped[str | None] = mapped_column(String(180), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    doctor: Mapped[str | None] = mapped_column(String(80), nullable=True)
    formula_relation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    formula_data: Mapped[str] = mapped_column(Text, default="{}")
    dosage_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("health_documents.id"), nullable=True)
    raw_user_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="recorded")


class Measurement(Base):
    __tablename__ = "measurements"
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("family_members.id"), index=True)
    type: Mapped[str] = mapped_column(String(40), index=True)
    value: Mapped[float] = mapped_column(Float)
    value2: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(30))
    measurement_context: Mapped[str] = mapped_column(String(40), default="unknown")
    measured_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)
    source: Mapped[str] = mapped_column(String(40), default="user_reported")
    raw_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class MedicalVisit(Base, TimestampMixin):
    __tablename__ = "medical_visits"
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("family_members.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="PREPARING", index=True)
    visit_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    symptom_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    medical_history_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    medication_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    measurement_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    questions_for_doctor: Mapped[str | None] = mapped_column(Text, nullable=True)
    doctor_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    doctor_confirmed_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    conversation_step: Mapped[int] = mapped_column(Integer, default=0)


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("family_members.id"), index=True)
    session_id: Mapped[str] = mapped_column(String(80), index=True)
    visit_id: Mapped[int | None] = mapped_column(ForeignKey("medical_visits.id"), nullable=True)
    role: Mapped[str] = mapped_column(String(20))
    text: Mapped[str] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class HealthDocument(Base):
    __tablename__ = "health_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("family_members.id"), index=True)
    document_type: Mapped[str] = mapped_column(String(40), default="other")
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    document_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    raw_extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="uploaded_document")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class CareTask(Base, TimestampMixin):
    __tablename__ = "care_tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("family_members.id"), index=True)
    task_type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    recurrence: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source: Mapped[str] = mapped_column(String(30), default="system")
    status: Mapped[str] = mapped_column(String(30), default="pending")


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("family_members.id"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    relationship: Mapped[str] = mapped_column(String(50))
    phone: Mapped[str] = mapped_column(String(40))
    priority: Mapped[int] = mapped_column(Integer, default=1)
    can_receive_alert: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class CheckInSchedule(Base, TimestampMixin):
    __tablename__ = "check_in_schedules"
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("family_members.id"), unique=True)
    morning_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    morning_time: Mapped[str] = mapped_column(String(5), default="08:30")
    afternoon_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    afternoon_time: Mapped[str] = mapped_column(String(5), default="13:30")
    evening_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    evening_time: Mapped[str] = mapped_column(String(5), default="19:30")
    skip_today: Mapped[bool] = mapped_column(Boolean, default=False)
    snooze_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class PendingAction(Base):
    __tablename__ = "pending_actions"
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("family_members.id"), index=True)
    session_id: Mapped[str] = mapped_column(String(80), index=True)
    action_type: Mapped[str] = mapped_column(String(50))
    payload: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class MemberHealthSetting(Base, TimestampMixin):
    __tablename__ = "member_health_settings"
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("family_members.id"), unique=True, index=True)
    western_prevention_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    tcm_health_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    tcm_enabled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    tcm_consent_version: Mapped[str | None] = mapped_column(String(30), nullable=True)
    tcm_depth: Mapped[str] = mapped_column(String(20), default="basic")


class HealthAnalysisRun(Base):
    __tablename__ = "health_analysis_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("family_members.id"), index=True)
    engine: Mapped[str] = mapped_column(String(30), index=True)
    period_days: Mapped[int] = mapped_column(Integer)
    current_start: Mapped[datetime] = mapped_column(DateTime)
    current_end: Mapped[datetime] = mapped_column(DateTime)
    baseline_start: Mapped[datetime] = mapped_column(DateTime)
    baseline_end: Mapped[datetime] = mapped_column(DateTime)
    engine_version: Mapped[str] = mapped_column(String(30))
    rule_set_version: Mapped[str] = mapped_column(String(30))
    trigger_type: Mapped[str] = mapped_column(String(40), default="manual")
    trigger_source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)


class HealthAnalysisResult(Base):
    __tablename__ = "health_analysis_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("health_analysis_runs.id"), index=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(40))
    trend: Mapped[str] = mapped_column(String(20), default="unknown")
    risk_level: Mapped[str] = mapped_column(String(30), index=True)
    summary: Mapped[str] = mapped_column(Text)
    uncertainty: Mapped[str] = mapped_column(Text, default="[]")
    suggestion: Mapped[str] = mapped_column(Text, default="[]")
    escalation_action: Mapped[str] = mapped_column(String(50), default="continue_monitoring")
    rule_ids: Mapped[str] = mapped_column(Text, default="[]")


class HealthEvidence(Base):
    __tablename__ = "health_evidence"
    id: Mapped[int] = mapped_column(primary_key=True)
    result_id: Mapped[int] = mapped_column(ForeignKey("health_analysis_results.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(40), index=True)
    source_id: Mapped[str] = mapped_column(String(120))
    recorded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    original_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text)
    confirmed_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[str] = mapped_column(String(20), default="medium")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class MedicalRule(Base, TimestampMixin):
    __tablename__ = "medical_rules"
    __table_args__ = (UniqueConstraint("rule_id", "rule_version", name="uq_medical_rule_version"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(80), index=True)
    rule_name: Mapped[str] = mapped_column(String(160))
    rule_version: Mapped[str] = mapped_column(String(30))
    category: Mapped[str] = mapped_column(String(50), index=True)
    condition: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(30))
    escalation_action: Mapped[str] = mapped_column(String(50))
    source: Mapped[str] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class PreventionItem(Base, TimestampMixin):
    __tablename__ = "prevention_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("family_members.id"), index=True)
    title: Mapped[str] = mapped_column(String(180))
    category: Mapped[str] = mapped_column(String(60), index=True)
    reason: Mapped[str] = mapped_column(Text)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="unknown", index=True)
    source_type: Mapped[str] = mapped_column(String(40))
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rule_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class HealthLogRevision(Base):
    __tablename__ = "health_log_revisions"
    id: Mapped[int] = mapped_column(primary_key=True)
    health_log_id: Mapped[int] = mapped_column(ForeignKey("health_logs.id"), index=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("family_members.id"), index=True)
    previous_raw_text: Mapped[str] = mapped_column(Text)
    previous_log_type: Mapped[str] = mapped_column(String(40))
    previous_structured_data: Mapped[str] = mapped_column(Text)
    previous_possible_emergency: Mapped[bool] = mapped_column(Boolean)
    revised_at: Mapped[datetime] = mapped_column(DateTime, default=now)
