"""初始化家庭健康数据表。

Revision ID: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _timestamps() -> list[sa.Column]:
    return [sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False)]


def upgrade() -> None:
    op.create_table("family_members", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(80), nullable=False), sa.Column("nickname", sa.String(80)), sa.Column("gender", sa.String(20)), sa.Column("birthday", sa.Date()), sa.Column("relationship", sa.String(50)), sa.Column("avatar", sa.String(255)), sa.Column("preferred_name", sa.String(80)), sa.Column("notes", sa.Text()), *_timestamps())
    op.create_table("health_profiles", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("member_id", sa.Integer(), sa.ForeignKey("family_members.id"), unique=True, nullable=False), sa.Column("known_conditions", sa.Text()), sa.Column("allergies", sa.Text()), sa.Column("past_history", sa.Text()), sa.Column("family_history", sa.Text()), sa.Column("medications", sa.Text()), sa.Column("height", sa.Float()), sa.Column("weight", sa.Float()), sa.Column("smoking_status", sa.String(40)), sa.Column("drinking_status", sa.String(40)), sa.Column("doctor_notes", sa.Text()), *_timestamps())
    op.create_table("health_logs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("member_id", sa.Integer(), sa.ForeignKey("family_members.id"), nullable=False), sa.Column("log_type", sa.String(40), nullable=False), sa.Column("raw_text", sa.Text(), nullable=False), sa.Column("structured_data", sa.Text(), nullable=False), sa.Column("source", sa.String(40), nullable=False), sa.Column("possible_emergency", sa.Boolean(), nullable=False), sa.Column("occurred_at", sa.DateTime(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_health_logs_member_id", "health_logs", ["member_id"])
    op.create_table("measurements", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("member_id", sa.Integer(), sa.ForeignKey("family_members.id"), nullable=False), sa.Column("type", sa.String(40), nullable=False), sa.Column("value", sa.Float(), nullable=False), sa.Column("value2", sa.Float()), sa.Column("unit", sa.String(30), nullable=False), sa.Column("measurement_context", sa.String(40), nullable=False), sa.Column("measured_at", sa.DateTime(), nullable=False), sa.Column("source", sa.String(40), nullable=False), sa.Column("raw_text", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_measurements_member_id", "measurements", ["member_id"])
    op.create_table("medical_visits", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("member_id", sa.Integer(), sa.ForeignKey("family_members.id"), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("visit_reason", sa.Text()), sa.Column("chief_complaint", sa.Text()), sa.Column("symptom_summary", sa.Text()), sa.Column("medical_history_snapshot", sa.Text()), sa.Column("medication_snapshot", sa.Text()), sa.Column("measurement_summary", sa.Text()), sa.Column("report_summary", sa.Text()), sa.Column("questions_for_doctor", sa.Text()), sa.Column("doctor_feedback", sa.Text()), sa.Column("doctor_confirmed_plan", sa.Text()), sa.Column("feedback_source", sa.String(50)), sa.Column("follow_up_date", sa.Date()), sa.Column("conversation_step", sa.Integer(), nullable=False), *_timestamps())
    op.create_index("ix_medical_visits_member_id", "medical_visits", ["member_id"])
    op.create_table("conversation_messages", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("member_id", sa.Integer(), sa.ForeignKey("family_members.id"), nullable=False), sa.Column("session_id", sa.String(80), nullable=False), sa.Column("visit_id", sa.Integer(), sa.ForeignKey("medical_visits.id")), sa.Column("role", sa.String(20), nullable=False), sa.Column("text", sa.Text(), nullable=False), sa.Column("intent", sa.String(50)), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_conversation_messages_session_id", "conversation_messages", ["session_id"])
    op.create_table("health_documents", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("member_id", sa.Integer(), sa.ForeignKey("family_members.id"), nullable=False), sa.Column("document_type", sa.String(40), nullable=False), sa.Column("file_name", sa.String(255), nullable=False), sa.Column("file_path", sa.String(500), nullable=False), sa.Column("document_date", sa.Date()), sa.Column("raw_extracted_text", sa.Text()), sa.Column("ai_summary", sa.Text()), sa.Column("source", sa.String(50), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("care_tasks", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("member_id", sa.Integer(), sa.ForeignKey("family_members.id"), nullable=False), sa.Column("task_type", sa.String(50), nullable=False), sa.Column("title", sa.String(150), nullable=False), sa.Column("description", sa.Text()), sa.Column("scheduled_at", sa.DateTime()), sa.Column("recurrence", sa.String(80)), sa.Column("source", sa.String(30), nullable=False), sa.Column("status", sa.String(30), nullable=False), *_timestamps())
    op.create_table("emergency_contacts", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("member_id", sa.Integer(), sa.ForeignKey("family_members.id"), nullable=False), sa.Column("name", sa.String(80), nullable=False), sa.Column("relationship", sa.String(50), nullable=False), sa.Column("phone", sa.String(40), nullable=False), sa.Column("priority", sa.Integer(), nullable=False), sa.Column("can_receive_alert", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("check_in_schedules", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("member_id", sa.Integer(), sa.ForeignKey("family_members.id"), unique=True, nullable=False), sa.Column("morning_enabled", sa.Boolean(), nullable=False), sa.Column("morning_time", sa.String(5), nullable=False), sa.Column("afternoon_enabled", sa.Boolean(), nullable=False), sa.Column("afternoon_time", sa.String(5), nullable=False), sa.Column("evening_enabled", sa.Boolean(), nullable=False), sa.Column("evening_time", sa.String(5), nullable=False), sa.Column("skip_today", sa.Boolean(), nullable=False), sa.Column("snooze_until", sa.DateTime()), *_timestamps())
    op.create_table("pending_actions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("member_id", sa.Integer(), sa.ForeignKey("family_members.id"), nullable=False), sa.Column("session_id", sa.String(80), nullable=False), sa.Column("action_type", sa.String(50), nullable=False), sa.Column("payload", sa.Text(), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))


def downgrade() -> None:
    for name in ("pending_actions", "check_in_schedules", "emergency_contacts", "care_tasks", "health_documents", "conversation_messages", "medical_visits", "measurements", "health_logs", "health_profiles", "family_members"):
        op.drop_table(name)

