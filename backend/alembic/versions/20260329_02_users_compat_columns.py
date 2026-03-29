"""compat columns for legacy users table

Revision ID: 20260329_02
Revises: 20260329_01
Create Date: 2026-03-29
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260329_02"
down_revision = "20260329_01"
branch_labels = None
depends_on = None


def _column_exists(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _index_exists(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return any(idx.get("name") == index_name for idx in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if "users" not in table_names:
        return

    if not _column_exists(inspector, "users", "department_id"):
        op.add_column("users", sa.Column("department_id", sa.Integer(), nullable=True))

    if not _column_exists(inspector, "users", "manager_id"):
        op.add_column("users", sa.Column("manager_id", sa.Integer(), nullable=True))

    inspector = sa.inspect(bind)

    if not _index_exists(inspector, "users", "ix_users_department_id"):
        op.create_index("ix_users_department_id", "users", ["department_id"], unique=False)

    if not _index_exists(inspector, "users", "ix_users_manager_id"):
        op.create_index("ix_users_manager_id", "users", ["manager_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if "users" not in table_names:
        return

    if _index_exists(inspector, "users", "ix_users_department_id"):
        op.drop_index("ix_users_department_id", table_name="users")

    if _index_exists(inspector, "users", "ix_users_manager_id"):
        op.drop_index("ix_users_manager_id", table_name="users")

    columns = {col["name"] for col in sa.inspect(bind).get_columns("users")}
    with op.batch_alter_table("users") as batch_op:
        if "department_id" in columns:
            batch_op.drop_column("department_id")
        if "manager_id" in columns:
            batch_op.drop_column("manager_id")
