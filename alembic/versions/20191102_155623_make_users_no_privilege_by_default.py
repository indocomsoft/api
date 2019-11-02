"""Make users no privilege by default

Revision ID: ce35232971d0
Revises: 550932fd8ea0
Create Date: 2019-11-02 15:56:23.903566

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "ce35232971d0"
down_revision = "550932fd8ea0"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("users", "can_buy", server_default="f")
    op.alter_column("users", "can_sell", server_default="f")
    op.alter_column("users", "is_committee", server_default="f")


def downgrade():
    op.alter_column("users", "can_buy", server_default="t")
    op.alter_column("users", "can_sell", server_default="t")
    op.alter_column("users", "is_committee", server_default="t")
