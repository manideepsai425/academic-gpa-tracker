"""Initial schema: users and academic_records

Revision ID: 20260709_143013
Revises:
Create Date: 2026-07-09 14:30:13

This migration was hand-written to match app/models exactly, since
this environment has no live Postgres instance to run
`alembic revision --autogenerate` against. If you'd rather generate it
fresh: delete this file, point DATABASE_URL at a running Postgres
instance, and run `alembic revision --autogenerate -m "initial schema"`
— it will produce an equivalent result from the models in app/models/.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260709_143013"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    record_type_enum = sa.Enum("SCHOOL", "INTERMEDIATE", "COLLEGE", name="recordtype")
    record_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "academic_records",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("period", sa.String(length=100), nullable=False),
        sa.Column("type", record_type_enum, nullable=False),
        sa.Column("gpa", sa.Float(), nullable=False),
        sa.Column("marks", sa.Float(), nullable=True),
        sa.Column("max_marks", sa.Float(), nullable=True),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_academic_records_id", "academic_records", ["id"])
    op.create_index("ix_academic_records_user_id", "academic_records", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_academic_records_user_id", table_name="academic_records")
    op.drop_index("ix_academic_records_id", table_name="academic_records")
    op.drop_table("academic_records")

    record_type_enum = sa.Enum("SCHOOL", "INTERMEDIATE", "COLLEGE", name="recordtype")
    record_type_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
