"""新增双轨健康守护、证据、规则、预防事项与纠错留痕。

Revision ID: 0004_health_guard
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_health_guard"
down_revision = "0003_medication_courses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "member_health_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("member_id", sa.Integer(), sa.ForeignKey("family_members.id"), nullable=False),
        sa.Column("western_prevention_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("tcm_health_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tcm_enabled_at", sa.DateTime()),
        sa.Column("tcm_consent_version", sa.String(30)),
        sa.Column("tcm_depth", sa.String(20), nullable=False, server_default="basic"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("member_id"),
    )
    op.create_index("ix_member_health_settings_member_id", "member_health_settings", ["member_id"], unique=True)
    op.create_table(
        "health_analysis_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("member_id", sa.Integer(), sa.ForeignKey("family_members.id"), nullable=False),
        sa.Column("engine", sa.String(30), nullable=False),
        sa.Column("period_days", sa.Integer(), nullable=False),
        sa.Column("current_start", sa.DateTime(), nullable=False),
        sa.Column("current_end", sa.DateTime(), nullable=False),
        sa.Column("baseline_start", sa.DateTime(), nullable=False),
        sa.Column("baseline_end", sa.DateTime(), nullable=False),
        sa.Column("engine_version", sa.String(30), nullable=False),
        sa.Column("rule_set_version", sa.String(30), nullable=False),
        sa.Column("trigger_type", sa.String(40), nullable=False, server_default="manual"),
        sa.Column("trigger_source_id", sa.Integer()),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_health_analysis_runs_member_id", "health_analysis_runs", ["member_id"])
    op.create_index("ix_health_analysis_runs_engine", "health_analysis_runs", ["engine"])
    op.create_index("ix_health_analysis_runs_generated_at", "health_analysis_runs", ["generated_at"])
    op.create_table(
        "health_analysis_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("health_analysis_runs.id"), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("trend", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("risk_level", sa.String(30), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("uncertainty", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("suggestion", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("escalation_action", sa.String(50), nullable=False, server_default="continue_monitoring"),
        sa.Column("rule_ids", sa.Text(), nullable=False, server_default="[]"),
    )
    op.create_index("ix_health_analysis_results_run_id", "health_analysis_results", ["run_id"])
    op.create_index("ix_health_analysis_results_category", "health_analysis_results", ["category"])
    op.create_index("ix_health_analysis_results_risk_level", "health_analysis_results", ["risk_level"])
    op.create_table(
        "health_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("result_id", sa.Integer(), sa.ForeignKey("health_analysis_results.id"), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("source_id", sa.String(120), nullable=False),
        sa.Column("recorded_at", sa.DateTime()),
        sa.Column("original_text", sa.Text()),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("confirmed_by_user", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("confidence", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_health_evidence_result_id", "health_evidence", ["result_id"])
    op.create_index("ix_health_evidence_source_type", "health_evidence", ["source_type"])
    op.create_table(
        "medical_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rule_id", sa.String(80), nullable=False),
        sa.Column("rule_name", sa.String(160), nullable=False),
        sa.Column("rule_version", sa.String(30), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("condition", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.String(30), nullable=False),
        sa.Column("escalation_action", sa.String(50), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime()),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("rule_id", "rule_version", name="uq_medical_rule_version"),
    )
    op.create_index("ix_medical_rules_rule_id", "medical_rules", ["rule_id"])
    op.create_index("ix_medical_rules_category", "medical_rules", ["category"])
    op.create_table(
        "prevention_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("member_id", sa.Integer(), sa.ForeignKey("family_members.id"), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("due_date", sa.Date()),
        sa.Column("status", sa.String(30), nullable=False, server_default="unknown"),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("source_reference", sa.String(255)),
        sa.Column("rule_id", sa.String(80)),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_prevention_items_member_id", "prevention_items", ["member_id"])
    op.create_index("ix_prevention_items_category", "prevention_items", ["category"])
    op.create_index("ix_prevention_items_status", "prevention_items", ["status"])
    op.create_table(
        "health_log_revisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("health_log_id", sa.Integer(), sa.ForeignKey("health_logs.id"), nullable=False),
        sa.Column("member_id", sa.Integer(), sa.ForeignKey("family_members.id"), nullable=False),
        sa.Column("previous_raw_text", sa.Text(), nullable=False),
        sa.Column("previous_log_type", sa.String(40), nullable=False),
        sa.Column("previous_structured_data", sa.Text(), nullable=False),
        sa.Column("previous_possible_emergency", sa.Boolean(), nullable=False),
        sa.Column("revised_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_health_log_revisions_health_log_id", "health_log_revisions", ["health_log_id"])
    op.create_index("ix_health_log_revisions_member_id", "health_log_revisions", ["member_id"])


def downgrade() -> None:
    # 仅用于显式人工回滚；正常升级流程不会自动删除任何健康数据。
    op.drop_table("health_log_revisions")
    op.drop_table("prevention_items")
    op.drop_table("medical_rules")
    op.drop_table("health_evidence")
    op.drop_table("health_analysis_results")
    op.drop_table("health_analysis_runs")
    op.drop_table("member_health_settings")
