"""Initial migration - create users table

Revision ID: 001
Revises:
Create Date: 2025-11-13

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("private_key", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("name"),
    )

    # Create indexes
    op.create_index(op.f("ix_users_name"), "users", ["name"], unique=False)
    op.create_index(
        op.f("ix_users_address"), "users", ["address"], unique=True
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f("ix_users_address"), table_name="users")
    op.drop_index(op.f("ix_users_name"), table_name="users")

    # Drop table
    op.drop_table("users")
