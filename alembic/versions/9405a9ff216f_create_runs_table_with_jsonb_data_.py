"""Create runs table with JSONB data storage

Revision ID: 9405a9ff216f
Revises:
Create Date: 2025-09-13 11:19:20.871004

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "9405a9ff216f"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create runs table with hybrid table fields + JSONB approach
    op.create_table(
        "runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.String(length=255), nullable=False),
        sa.Column("trace_id", sa.String(length=255), nullable=False),
        sa.Column("project", sa.String(length=255), nullable=False),
        sa.Column("run_date", sa.Date(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id"),
        # Ensure consistency between table fields and JSONB data
        sa.CheckConstraint("data->>'run_id' = run_id", name="check_run_id_matches"),
        sa.CheckConstraint("data->>'trace_id' = trace_id", name="check_trace_id_matches"),
        sa.CheckConstraint("data->>'project' = project", name="check_project_matches"),
        sa.CheckConstraint("(data->>'run_date')::date = run_date", name="check_run_date_matches"),
    )

    # Create indexes for efficient querying
    op.create_index(op.f("ix_runs_run_id"), "runs", ["run_id"], unique=True)
    op.create_index(op.f("ix_runs_trace_id"), "runs", ["trace_id"], unique=False)
    op.create_index(op.f("ix_runs_project"), "runs", ["project"], unique=False)
    op.create_index(op.f("ix_runs_run_date"), "runs", ["run_date"], unique=False)
    op.create_index(op.f("ix_runs_project_run_date"), "runs", ["project", "run_date"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes first
    op.drop_index(op.f("ix_runs_project_run_date"), table_name="runs")
    op.drop_index(op.f("ix_runs_run_date"), table_name="runs")
    op.drop_index(op.f("ix_runs_project"), table_name="runs")
    op.drop_index(op.f("ix_runs_trace_id"), table_name="runs")
    op.drop_index(op.f("ix_runs_run_id"), table_name="runs")

    # Drop table
    op.drop_table("runs")
