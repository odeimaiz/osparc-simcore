"""new tags priority column

Revision ID: 8a742f3efdd9
Revises: 10729e07000d
Create Date: 2024-10-02 15:23:27.446241+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8a742f3efdd9"
down_revision = "10729e07000d"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("tags", sa.Column("priority", sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("tags", "priority")
    # ### end Alembic commands ###