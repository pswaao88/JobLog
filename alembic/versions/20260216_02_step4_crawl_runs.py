"""step4 crawl runs

Revision ID: 20260216_02
Revises: 20260216_01
Create Date: 2026-02-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260216_02"
down_revision: Union[str, Sequence[str], None] = "20260216_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

run_status_enum = postgresql.ENUM(
    "running",
    "success",
    "partial_fail",
    "failed",
    name="run_status_enum",
    create_type=False,
)


def upgrade() -> None:
    op.create_table(
        "crawl_runs",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("source_id", sa.BigInteger(), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("finished_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("status", run_status_enum, nullable=False, server_default=sa.text("'running'")),
        sa.Column("fetched_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("inserted_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name="fk_crawl_runs_source_id_sources", ondelete="SET NULL"),
    )
    op.create_index("idx_crawl_runs_source_started", "crawl_runs", ["source_id", "started_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_crawl_runs_source_started", table_name="crawl_runs")
    op.drop_table("crawl_runs")
