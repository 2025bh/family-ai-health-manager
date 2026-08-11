"""扩展个人健康档案，保留结构化内容与原始文本。

Revision ID: 0002_extended_member_profile
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_extended_member_profile"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("health_profiles", sa.Column("profile_version", sa.String(30), nullable=True))
    op.add_column("health_profiles", sa.Column("occupation", sa.String(120), nullable=True))
    op.add_column("health_profiles", sa.Column("profile_data", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("health_profiles", sa.Column("raw_profile_text", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("health_profiles", "raw_profile_text")
    op.drop_column("health_profiles", "profile_data")
    op.drop_column("health_profiles", "occupation")
    op.drop_column("health_profiles", "profile_version")
