# First Alembic migration: creates the cached_vulnerabilities table.
import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None  # this is the very first migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cached_vulnerabilities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("package_key", sa.String(200), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("payload", sa.Text, nullable=False),
        sa.Column("fetched_at", sa.DateTime, nullable=False),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("package_key", "source", name="uq_cached_pkg_source"),
    )
    op.create_index("ix_cached_vulnerabilities_package_key", "cached_vulnerabilities", ["package_key"])


def downgrade() -> None:
    op.drop_index("ix_cached_vulnerabilities_package_key", table_name="cached_vulnerabilities")
    op.drop_table("cached_vulnerabilities")
