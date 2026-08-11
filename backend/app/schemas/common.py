from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MemberCreate(BaseModel):
    name: str
    nickname: str | None = None
    gender: str | None = None
    birthday: date | None = None
    relationship: str | None = None
    preferred_name: str | None = None
    notes: str | None = None


class MemberRead(ORMModel, MemberCreate):
    id: int
    created_at: datetime
    updated_at: datetime


class MemberUpdate(BaseModel):
    name: str | None = None
    nickname: str | None = None
    gender: str | None = None
    birthday: date | None = None
    relationship: str | None = None
    preferred_name: str | None = None
    notes: str | None = None


class ProfileUpdate(BaseModel):
    known_conditions: str | None = None
    allergies: str | None = None
    past_history: str | None = None
    family_history: str | None = None
    medications: str | None = None
    height: float | None = None
    weight: float | None = None
    smoking_status: str | None = None
    drinking_status: str | None = None
    doctor_notes: str | None = None
    profile_version: str | None = None
    occupation: str | None = None
    profile_data: dict[str, Any] | None = None
    raw_profile_text: str | None = None


class VoiceMessageIn(BaseModel):
    member_id: int
    text: str = Field(min_length=1, max_length=3000)
    session_id: str | None = None
    gateway: str = "web"


class VoiceMessageOut(BaseModel):
    session_id: str
    intent: str
    reply: str
    actions: list[dict[str, Any]] = []
    data: dict[str, Any] = {}
    possible_emergency: bool = False


class HealthLogCreate(BaseModel):
    member_id: int
    log_type: str
    raw_text: str
    structured_data: dict[str, Any] = {}
    source: str = "user_reported"
    source_key: str | None = None
    occurred_at: datetime | None = None


class HealthLogUpdate(BaseModel):
    raw_text: str = Field(min_length=1, max_length=3000)


class MedicationCourseCreate(BaseModel):
    member_id: int
    course_number: int
    prescription_date: date | None = None
    hospital: str | None = None
    department: str | None = None
    doctor: str | None = None
    formula_relation: str | None = None
    formula_data: dict[str, Any] = {}
    dosage_instructions: str | None = None
    source_document_id: int | None = None
    raw_user_text: str | None = None
    status: str = "recorded"


class MeasurementCreate(BaseModel):
    member_id: int
    type: str
    value: float
    value2: float | None = None
    unit: str
    measurement_context: str = "unknown"
    raw_text: str
    source: str = "user_reported"


class ContactCreate(BaseModel):
    member_id: int
    name: str
    relationship: str
    phone: str
    priority: int = 1
    can_receive_alert: bool = True


class TaskCreate(BaseModel):
    member_id: int
    task_type: str
    title: str
    description: str | None = None
    scheduled_at: datetime | None = None
    recurrence: str | None = None
    source: str = "family"


class TaskUpdate(BaseModel):
    status: str | None = None
    title: str | None = None
    description: str | None = None
    scheduled_at: datetime | None = None


class VisitReviewUpdate(BaseModel):
    key: str
    value: str = Field(min_length=1, max_length=3000)


class ScheduleUpdate(BaseModel):
    morning_enabled: bool = True
    morning_time: str = "08:30"
    afternoon_enabled: bool = False
    afternoon_time: str = "13:30"
    evening_enabled: bool = True
    evening_time: str = "19:30"
    skip_today: bool = False
    snooze_until: datetime | None = None


class FamilyNotificationIn(BaseModel):
    member_id: int
    message: str = Field(min_length=1, max_length=1000)
    confirm: bool = False
