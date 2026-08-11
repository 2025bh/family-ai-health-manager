"""新增处方疗程表。

Revision ID: 0003_medication_courses
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_medication_courses"
down_revision = "0002_extended_member_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("health_logs", sa.Column("source_key", sa.String(120), nullable=True))
    op.create_index("uq_health_logs_source_key", "health_logs", ["source_key"], unique=True)
    op.create_table(
        "medication_courses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("member_id", sa.Integer(), sa.ForeignKey("family_members.id"), nullable=False),
        sa.Column("course_number", sa.Integer(), nullable=False),
        sa.Column("prescription_date", sa.Date()),
        sa.Column("hospital", sa.String(180)),
        sa.Column("department", sa.String(100)),
        sa.Column("doctor", sa.String(80)),
        sa.Column("formula_relation", sa.String(120)),
        sa.Column("formula_data", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("dosage_instructions", sa.Text()),
        sa.Column("source_document_id", sa.Integer(), sa.ForeignKey("health_documents.id")),
        sa.Column("raw_user_text", sa.Text()),
        sa.Column("status", sa.String(30), nullable=False, server_default="recorded"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("member_id", "course_number", name="uq_medication_course_member_number"),
    )
    op.create_index("ix_medication_courses_member_id", "medication_courses", ["member_id"])
    op.create_index("ix_medication_courses_course_number", "medication_courses", ["course_number"])


def downgrade() -> None:
    op.drop_index("ix_medication_courses_course_number", table_name="medication_courses")
    op.drop_index("ix_medication_courses_member_id", table_name="medication_courses")
    op.drop_table("medication_courses")
    op.drop_index("uq_health_logs_source_key", table_name="health_logs")
    op.drop_column("health_logs", "source_key")
