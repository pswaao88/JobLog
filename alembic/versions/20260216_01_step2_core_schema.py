"""step2 core schema

Revision ID: 20260216_01
Revises: 
Create Date: 2026-02-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260216_01"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


employment_type_enum = postgresql.ENUM(
    "intern_experience",
    "intern_convertible",
    "new_grad",
    "experienced",
    "unknown",
    name="employment_type_enum",
)

role_type_enum = postgresql.ENUM(
    "backend",
    "frontend",
    "fullstack",
    "data",
    "mobile",
    "devops",
    "unknown",
    name="role_type_enum",
)

run_status_enum = postgresql.ENUM(
    "running",
    "success",
    "partial_fail",
    "failed",
    name="run_status_enum",
)


def upgrade() -> None:
    bind = op.get_bind()
    employment_type_enum.create(bind, checkfirst=True)
    role_type_enum.create(bind, checkfirst=True)
    run_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "sources",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("crawl_interval_min", sa.Integer(), nullable=False, server_default=sa.text("360")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("code", name="uq_sources_code"),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("source_job_id", sa.String(length=255), nullable=True),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description_text", sa.Text(), nullable=True),
        sa.Column("location_text", sa.String(length=255), nullable=True),
        sa.Column("employment_text_raw", sa.String(length=255), nullable=True),
        sa.Column("experience_text_raw", sa.String(length=255), nullable=True),
        sa.Column("tech_stack_text", sa.Text(), nullable=True),
        sa.Column("salary_text", sa.String(length=255), nullable=True),
        sa.Column("posted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deadline_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("first_seen_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("last_seen_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name="fk_jobs_source_id_sources", ondelete="RESTRICT"),
        sa.UniqueConstraint("canonical_url", name="uq_jobs_canonical_url"),
        sa.UniqueConstraint("source_id", "source_job_id", name="uq_jobs_source_id_source_job_id"),
    )
    op.create_index("idx_jobs_active", "jobs", ["is_active"], unique=False)
    op.create_index("idx_jobs_posted_at", "jobs", ["posted_at"], unique=False)
    op.create_index("idx_jobs_deadline_at", "jobs", ["deadline_at"], unique=False)
    op.create_index("idx_jobs_company_title", "jobs", ["company_name", "title"], unique=False)

    op.create_table(
        "classification_rules",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("rule_version", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("target_value", sa.String(length=100), nullable=False),
        sa.Column("keyword", sa.String(length=100), nullable=False),
        sa.Column("match_type", sa.String(length=20), nullable=False, server_default=sa.text("'contains'")),
        sa.Column("priority", sa.Integer(), nullable=False, server_default=sa.text("100")),
        sa.Column("weight", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_negation", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint(
            "rule_version",
            "category",
            "target_value",
            "keyword",
            "is_negation",
            name="uq_classification_rules_unique_set",
        ),
    )
    op.create_index(
        "idx_rules_active",
        "classification_rules",
        ["rule_version", "category", "is_active", "priority"],
        unique=False,
    )

    op.create_table(
        "job_classifications",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("job_id", sa.BigInteger(), nullable=False),
        sa.Column("rule_version", sa.String(length=50), nullable=False),
        sa.Column("employment_type", employment_type_enum, nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("role_type", role_type_enum, nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("new_grad_score", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False, server_default=sa.text("0.500")),
        sa.Column("matched_keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("new_grad_score BETWEEN 0 AND 100", name="ck_job_classifications_new_grad_score"),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_job_classifications_confidence"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], name="fk_job_classifications_job_id_jobs", ondelete="CASCADE"),
        sa.UniqueConstraint("job_id", "rule_version", name="uq_job_classifications_job_id_rule_version"),
    )
    op.create_index("idx_job_classifications_employment", "job_classifications", ["employment_type"], unique=False)
    op.create_index("idx_job_classifications_role", "job_classifications", ["role_type"], unique=False)
    op.create_index("idx_job_classifications_score", "job_classifications", ["new_grad_score"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_job_classifications_score", table_name="job_classifications")
    op.drop_index("idx_job_classifications_role", table_name="job_classifications")
    op.drop_index("idx_job_classifications_employment", table_name="job_classifications")
    op.drop_table("job_classifications")

    op.drop_index("idx_rules_active", table_name="classification_rules")
    op.drop_table("classification_rules")

    op.drop_index("idx_jobs_company_title", table_name="jobs")
    op.drop_index("idx_jobs_deadline_at", table_name="jobs")
    op.drop_index("idx_jobs_posted_at", table_name="jobs")
    op.drop_index("idx_jobs_active", table_name="jobs")
    op.drop_table("jobs")

    op.drop_table("sources")

    bind = op.get_bind()
    run_status_enum.drop(bind, checkfirst=True)
    role_type_enum.drop(bind, checkfirst=True)
    employment_type_enum.drop(bind, checkfirst=True)
