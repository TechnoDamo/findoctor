"""link transfers to ledger transactions

Revision ID: 20260529_0002
Revises: 20260529_0001
Create Date: 2026-05-29
"""

from __future__ import annotations

from alembic import op

revision = "20260529_0002"
down_revision = "20260529_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE transfer_leg AS ENUM ('debit', 'credit')")
    op.execute("ALTER TABLE transactions ADD COLUMN transfer_id UUID")
    op.execute("ALTER TABLE transactions ADD COLUMN transfer_leg transfer_leg")

    op.execute("CREATE INDEX ix_transactions_transfer_id ON transactions (transfer_id)")
    op.execute("""
        ALTER TABLE transactions
        ADD CONSTRAINT uq_transactions_transfer_id_transfer_leg
        UNIQUE (transfer_id, transfer_leg)
    """)
    op.execute("""
        ALTER TABLE transactions
        ADD CONSTRAINT fk_transactions_transfer_id
        FOREIGN KEY (transfer_id) REFERENCES transfers (id)
    """)
    op.execute("""
        ALTER TABLE transactions
        ADD CONSTRAINT ck_transactions_transfer_link_complete
        CHECK (
            (transfer_id IS NULL AND transfer_leg IS NULL)
            OR (
                transfer_id IS NOT NULL
                AND transfer_leg IS NOT NULL
                AND type = 'transfer'
            )
        )
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE transactions DROP CONSTRAINT IF EXISTS ck_transactions_transfer_link_complete")
    op.execute("ALTER TABLE transactions DROP CONSTRAINT IF EXISTS fk_transactions_transfer_id")
    op.execute("ALTER TABLE transactions DROP CONSTRAINT IF EXISTS uq_transactions_transfer_id_transfer_leg")
    op.execute("DROP INDEX IF EXISTS ix_transactions_transfer_id")
    op.execute("ALTER TABLE transactions DROP COLUMN IF EXISTS transfer_leg")
    op.execute("ALTER TABLE transactions DROP COLUMN IF EXISTS transfer_id")
    op.execute("DROP TYPE IF EXISTS transfer_leg")
