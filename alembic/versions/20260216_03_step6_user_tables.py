"""step6 bookmarks and applications

Revision ID: 20260216_03
Revises: 20260216_02
Create Date: 2026-02-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260216_03"
down_revision: Union[str, Sequence[str], None] = "20260216_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bookmarks",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("job_id", sa.BigInteger(), nullable=False),
        sa.Column("memo", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], name="fk_bookmarks_job_id_jobs", ondelete="CASCADE"),
        sa.UniqueConstraint("job_id", name="uq_bookmarks_job_id"),
    )

    op.create_table(
        "applications",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("job_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default=sa.text("'planned'")),
        sa.Column("applied_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], name="fk_applications_job_id_jobs", ondelete="CASCADE"),
        sa.UniqueConstraint("job_id", name="uq_applications_job_id"),
    )


def downgrade() -> None:
    op.drop_table("applications")
    op.drop_table("bookmarks")
