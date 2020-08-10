"""add service metad data and access right tables


Revision ID: f4fda75c0df0
Revises: 31f0ab4a338b
Create Date: 2020-08-03 13:04:05.565295+00:00

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

# revision identifiers, used by Alembic.
revision = "f4fda75c0df0"
down_revision = "31f0ab4a338b"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "services_meta_data",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("owner", sa.BigInteger(), nullable=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.String, nullable=False),
        sa.Column("thumbnail", sa.String, nullable=True),
        sa.Column(
            "classifiers",
            ARRAY(sa.String, dimensions=1),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "modified", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["owner"],
            ["groups.gid"],
            name="fk_services_meta_data_gid_groups",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("key", "version", name="services_meta_data_pk"),
    )
    op.create_table(
        "services_access_rights",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("gid", sa.BigInteger(), nullable=False),
        sa.Column(
            "execute_access",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "write_access",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "modified", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["gid"],
            ["groups.gid"],
            name="fk_services_gid_groups",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["key", "version"],
            ["services_meta_data.key", "services_meta_data.version"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("key", "version", "gid", name="services_access_pk"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("services_access_rights")
    op.drop_table("services_meta_data")
    # ### end Alembic commands ###
