"""initial schema

Revision ID: 20260529_0001
Revises:
Create Date: 2026-05-29
"""

from __future__ import annotations

from alembic import op

revision = "20260529_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE category_type AS ENUM ('income', 'expense')")
    op.execute("CREATE TYPE transaction_type AS ENUM ('income', 'expense', 'transfer')")
    op.execute(
        "CREATE TYPE recurring_operation_type AS ENUM "
        "('income', 'expense', 'transfer', 'liability_payment')"
    )
    op.execute("CREATE TYPE recurring_frequency AS ENUM ('daily', 'weekly', 'monthly', 'yearly')")
    op.execute("CREATE TYPE risk_level AS ENUM ('low', 'medium', 'high', 'unknown')")
    op.execute("CREATE TYPE interest_type AS ENUM ('fixed', 'variable', 'promotional', 'none')")
    op.execute(
        "CREATE TYPE liability_status AS ENUM "
        "('active', 'paid_off', 'defaulted', 'refinanced', 'closed')"
    )

    op.execute("""
        CREATE TABLE users (
            id UUID PRIMARY KEY,
            email VARCHAR NOT NULL UNIQUE,
            phone VARCHAR,
            password_hash VARCHAR NOT NULL,
            first_name VARCHAR,
            last_name VARCHAR,
            country VARCHAR,
            base_currency VARCHAR NOT NULL,
            timezone VARCHAR NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)

    op.execute("""
        CREATE TABLE account_types (
            id UUID PRIMARY KEY,
            code VARCHAR NOT NULL UNIQUE,
            name VARCHAR NOT NULL,
            description TEXT
        )
    """)

    op.execute("""
        CREATE TABLE provider_types (
            id UUID PRIMARY KEY,
            code VARCHAR NOT NULL UNIQUE,
            name VARCHAR NOT NULL,
            description TEXT
        )
    """)

    op.execute("""
        CREATE TABLE financial_institutions (
            id UUID PRIMARY KEY,
            name VARCHAR NOT NULL,
            country VARCHAR,
            website_url VARCHAR,
            logo_url VARCHAR,
            integration_key VARCHAR,
            risk_level risk_level NOT NULL DEFAULT 'unknown',
            is_active BOOLEAN NOT NULL DEFAULT true,
            CONSTRAINT uq_financial_institutions_name_country UNIQUE (name, country)
        )
    """)
    op.execute("CREATE INDEX ix_financial_institutions_integration_key ON financial_institutions (integration_key)")

    op.execute("""
        CREATE TABLE financial_institution_provider_types (
            financial_institution_id UUID NOT NULL,
            provider_type_id UUID NOT NULL,
            PRIMARY KEY (financial_institution_id, provider_type_id)
        )
    """)

    op.execute("""
        CREATE TABLE liability_types (
            id UUID PRIMARY KEY,
            code VARCHAR NOT NULL UNIQUE,
            name VARCHAR NOT NULL,
            description TEXT,
            is_secured BOOLEAN NOT NULL DEFAULT false
        )
    """)

    op.execute("""
        CREATE TABLE asset_types (
            id UUID PRIMARY KEY,
            code VARCHAR NOT NULL UNIQUE,
            name VARCHAR NOT NULL,
            description TEXT
        )
    """)

    op.execute("""
        CREATE TABLE accounts (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL,
            account_type_id UUID NOT NULL,
            institution_id UUID,
            name VARCHAR NOT NULL,
            institution_name VARCHAR,
            currency VARCHAR NOT NULL,
            balance DECIMAL NOT NULL DEFAULT 0,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)
    op.execute("CREATE INDEX ix_accounts_user_id ON accounts (user_id)")
    op.execute("CREATE INDEX ix_accounts_account_type_id ON accounts (account_type_id)")
    op.execute("CREATE INDEX ix_accounts_institution_id ON accounts (institution_id)")

    op.execute("""
        CREATE TABLE categories (
            id UUID PRIMARY KEY,
            parent_id UUID,
            type category_type NOT NULL,
            name VARCHAR NOT NULL,
            description TEXT
        )
    """)
    op.execute("CREATE INDEX ix_categories_parent_id ON categories (parent_id)")
    op.execute("CREATE INDEX ix_categories_type_name ON categories (type, name)")

    op.execute("""
        CREATE TABLE merchants (
            id UUID PRIMARY KEY,
            name VARCHAR NOT NULL,
            category VARCHAR,
            country VARCHAR,
            risk_level risk_level NOT NULL DEFAULT 'unknown'
        )
    """)
    op.execute("CREATE INDEX ix_merchants_name_country ON merchants (name, country)")

    op.execute("""
        CREATE TABLE transactions (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL,
            account_id UUID NOT NULL,
            category_id UUID,
            type transaction_type NOT NULL,
            amount DECIMAL NOT NULL,
            currency VARCHAR NOT NULL,
            transaction_datetime TIMESTAMP NOT NULL,
            description TEXT,
            merchant_id UUID,
            merchant_name VARCHAR,
            geo_location VARCHAR,
            recurring_transaction_id UUID,
            external_id VARCHAR,
            created_at TIMESTAMP NOT NULL,
            CONSTRAINT uq_transactions_account_external_id UNIQUE (account_id, external_id)
        )
    """)
    op.execute("CREATE INDEX ix_transactions_user_id ON transactions (user_id)")
    op.execute("CREATE INDEX ix_transactions_account_id ON transactions (account_id)")
    op.execute("CREATE INDEX ix_transactions_category_id ON transactions (category_id)")
    op.execute("CREATE INDEX ix_transactions_merchant_id ON transactions (merchant_id)")
    op.execute("CREATE INDEX ix_transactions_recurring_transaction_id ON transactions (recurring_transaction_id)")
    op.execute("CREATE INDEX ix_transactions_transaction_datetime ON transactions (transaction_datetime)")

    op.execute("""
        CREATE TABLE recurring_transactions (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL,
            account_id UUID NOT NULL,
            category_id UUID,
            liability_id UUID,
            operation_type recurring_operation_type NOT NULL,
            name VARCHAR NOT NULL,
            expected_amount DECIMAL,
            currency VARCHAR,
            frequency recurring_frequency NOT NULL,
            interval_count INTEGER NOT NULL DEFAULT 1,
            day_of_month INTEGER,
            start_date DATE,
            end_date DATE,
            next_payment_date DATE,
            auto_generated BOOLEAN NOT NULL DEFAULT false,
            confidence_score DECIMAL,
            is_active BOOLEAN NOT NULL DEFAULT true
        )
    """)
    op.execute("CREATE INDEX ix_recurring_transactions_user_id ON recurring_transactions (user_id)")
    op.execute("CREATE INDEX ix_recurring_transactions_account_id ON recurring_transactions (account_id)")
    op.execute("CREATE INDEX ix_recurring_transactions_category_id ON recurring_transactions (category_id)")
    op.execute("CREATE INDEX ix_recurring_transactions_liability_id ON recurring_transactions (liability_id)")
    op.execute("CREATE INDEX ix_recurring_transactions_next_payment_date ON recurring_transactions (next_payment_date)")

    op.execute("""
        CREATE TABLE transfers (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL,
            from_account_id UUID NOT NULL,
            to_account_id UUID NOT NULL,
            amount DECIMAL NOT NULL,
            currency VARCHAR NOT NULL,
            transaction_datetime TIMESTAMP NOT NULL,
            description TEXT
        )
    """)
    op.execute("CREATE INDEX ix_transfers_user_id ON transfers (user_id)")
    op.execute("CREATE INDEX ix_transfers_from_account_id ON transfers (from_account_id)")
    op.execute("CREATE INDEX ix_transfers_to_account_id ON transfers (to_account_id)")
    op.execute("CREATE INDEX ix_transfers_transaction_datetime ON transfers (transaction_datetime)")

    op.execute("""
        CREATE TABLE assets (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL,
            asset_type_id UUID NOT NULL,
            name VARCHAR NOT NULL,
            estimated_value DECIMAL NOT NULL DEFAULT 0,
            currency VARCHAR NOT NULL,
            purchase_price DECIMAL,
            purchase_date DATE,
            monthly_cost DECIMAL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)
    op.execute("CREATE INDEX ix_assets_user_id ON assets (user_id)")
    op.execute("CREATE INDEX ix_assets_asset_type_id ON assets (asset_type_id)")

    op.execute("""
        CREATE TABLE liabilities (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL,
            liability_type_id UUID NOT NULL,
            linked_account_id UUID,
            collateral_asset_id UUID,
            name VARCHAR NOT NULL,
            creditor_institution_id UUID,
            creditor_name VARCHAR,
            original_amount DECIMAL,
            current_balance DECIMAL NOT NULL DEFAULT 0,
            currency VARCHAR NOT NULL,
            interest_rate DECIMAL,
            interest_type interest_type,
            minimum_payment_amount DECIMAL,
            regular_payment_amount DECIMAL,
            payment_due_day INTEGER,
            start_date DATE,
            maturity_date DATE,
            status liability_status NOT NULL DEFAULT 'active',
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)
    op.execute("CREATE INDEX ix_liabilities_user_id ON liabilities (user_id)")
    op.execute("CREATE INDEX ix_liabilities_liability_type_id ON liabilities (liability_type_id)")
    op.execute("CREATE INDEX ix_liabilities_linked_account_id ON liabilities (linked_account_id)")
    op.execute("CREATE INDEX ix_liabilities_collateral_asset_id ON liabilities (collateral_asset_id)")
    op.execute("CREATE INDEX ix_liabilities_creditor_institution_id ON liabilities (creditor_institution_id)")
    op.execute("CREATE INDEX ix_liabilities_status ON liabilities (status)")

    op.execute("""
        CREATE TABLE liability_payments (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL,
            liability_id UUID NOT NULL,
            transaction_id UUID NOT NULL UNIQUE,
            recurring_transaction_id UUID,
            payment_date DATE NOT NULL,
            total_amount DECIMAL NOT NULL,
            principal_amount DECIMAL,
            interest_amount DECIMAL,
            fee_amount DECIMAL,
            currency VARCHAR NOT NULL,
            balance_after_payment DECIMAL,
            created_at TIMESTAMP NOT NULL
        )
    """)
    op.execute("CREATE INDEX ix_liability_payments_user_id ON liability_payments (user_id)")
    op.execute("CREATE INDEX ix_liability_payments_liability_id ON liability_payments (liability_id)")
    op.execute("CREATE INDEX ix_liability_payments_recurring_transaction_id ON liability_payments (recurring_transaction_id)")
    op.execute("CREATE INDEX ix_liability_payments_payment_date ON liability_payments (payment_date)")

    op.execute("""
        CREATE TABLE financial_goals (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL,
            name VARCHAR NOT NULL,
            target_amount DECIMAL NOT NULL,
            current_amount DECIMAL NOT NULL DEFAULT 0,
            deadline DATE,
            priority INTEGER,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)
    op.execute("CREATE INDEX ix_financial_goals_user_id ON financial_goals (user_id)")
    op.execute("CREATE INDEX ix_financial_goals_deadline ON financial_goals (deadline)")
    op.execute("CREATE INDEX ix_financial_goals_priority ON financial_goals (priority)")

    op.execute("""
        CREATE TABLE tags (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL,
            name VARCHAR NOT NULL,
            CONSTRAINT uq_tags_user_id_name UNIQUE (user_id, name)
        )
    """)

    op.execute("""
        CREATE TABLE transaction_tags (
            transaction_id UUID NOT NULL,
            tag_id UUID NOT NULL,
            PRIMARY KEY (transaction_id, tag_id)
        )
    """)

    op.execute("""
        CREATE TABLE daily_financial_snapshots (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL,
            snapshot_date DATE NOT NULL,
            total_cash DECIMAL NOT NULL DEFAULT 0,
            total_assets DECIMAL NOT NULL DEFAULT 0,
            total_liabilities DECIMAL NOT NULL DEFAULT 0,
            net_worth DECIMAL NOT NULL DEFAULT 0,
            monthly_income DECIMAL NOT NULL DEFAULT 0,
            monthly_expenses DECIMAL NOT NULL DEFAULT 0,
            savings_rate DECIMAL,
            CONSTRAINT uq_daily_financial_snapshots_user_snapshot_date UNIQUE (user_id, snapshot_date)
        )
    """)

    op.execute("""
        ALTER TABLE financial_institution_provider_types
        ADD CONSTRAINT fk_fipt_financial_institution_id
        FOREIGN KEY (financial_institution_id) REFERENCES financial_institutions (id)
    """)
    op.execute("""
        ALTER TABLE financial_institution_provider_types
        ADD CONSTRAINT fk_fipt_provider_type_id
        FOREIGN KEY (provider_type_id) REFERENCES provider_types (id)
    """)
    op.execute("ALTER TABLE accounts ADD CONSTRAINT fk_accounts_user_id FOREIGN KEY (user_id) REFERENCES users (id)")
    op.execute("ALTER TABLE accounts ADD CONSTRAINT fk_accounts_account_type_id FOREIGN KEY (account_type_id) REFERENCES account_types (id)")
    op.execute("ALTER TABLE accounts ADD CONSTRAINT fk_accounts_institution_id FOREIGN KEY (institution_id) REFERENCES financial_institutions (id)")
    op.execute("ALTER TABLE categories ADD CONSTRAINT fk_categories_parent_id FOREIGN KEY (parent_id) REFERENCES categories (id)")
    op.execute("ALTER TABLE transactions ADD CONSTRAINT fk_transactions_user_id FOREIGN KEY (user_id) REFERENCES users (id)")
    op.execute("ALTER TABLE transactions ADD CONSTRAINT fk_transactions_account_id FOREIGN KEY (account_id) REFERENCES accounts (id)")
    op.execute("ALTER TABLE transactions ADD CONSTRAINT fk_transactions_category_id FOREIGN KEY (category_id) REFERENCES categories (id)")
    op.execute("ALTER TABLE transactions ADD CONSTRAINT fk_transactions_merchant_id FOREIGN KEY (merchant_id) REFERENCES merchants (id)")
    op.execute("ALTER TABLE transactions ADD CONSTRAINT fk_transactions_recurring_transaction_id FOREIGN KEY (recurring_transaction_id) REFERENCES recurring_transactions (id)")
    op.execute("ALTER TABLE recurring_transactions ADD CONSTRAINT fk_recurring_transactions_user_id FOREIGN KEY (user_id) REFERENCES users (id)")
    op.execute("ALTER TABLE recurring_transactions ADD CONSTRAINT fk_recurring_transactions_account_id FOREIGN KEY (account_id) REFERENCES accounts (id)")
    op.execute("ALTER TABLE recurring_transactions ADD CONSTRAINT fk_recurring_transactions_category_id FOREIGN KEY (category_id) REFERENCES categories (id)")
    op.execute("ALTER TABLE recurring_transactions ADD CONSTRAINT fk_recurring_transactions_liability_id FOREIGN KEY (liability_id) REFERENCES liabilities (id)")
    op.execute("ALTER TABLE transfers ADD CONSTRAINT fk_transfers_user_id FOREIGN KEY (user_id) REFERENCES users (id)")
    op.execute("ALTER TABLE transfers ADD CONSTRAINT fk_transfers_from_account_id FOREIGN KEY (from_account_id) REFERENCES accounts (id)")
    op.execute("ALTER TABLE transfers ADD CONSTRAINT fk_transfers_to_account_id FOREIGN KEY (to_account_id) REFERENCES accounts (id)")
    op.execute("ALTER TABLE assets ADD CONSTRAINT fk_assets_user_id FOREIGN KEY (user_id) REFERENCES users (id)")
    op.execute("ALTER TABLE assets ADD CONSTRAINT fk_assets_asset_type_id FOREIGN KEY (asset_type_id) REFERENCES asset_types (id)")
    op.execute("ALTER TABLE liabilities ADD CONSTRAINT fk_liabilities_user_id FOREIGN KEY (user_id) REFERENCES users (id)")
    op.execute("ALTER TABLE liabilities ADD CONSTRAINT fk_liabilities_liability_type_id FOREIGN KEY (liability_type_id) REFERENCES liability_types (id)")
    op.execute("ALTER TABLE liabilities ADD CONSTRAINT fk_liabilities_linked_account_id FOREIGN KEY (linked_account_id) REFERENCES accounts (id)")
    op.execute("ALTER TABLE liabilities ADD CONSTRAINT fk_liabilities_collateral_asset_id FOREIGN KEY (collateral_asset_id) REFERENCES assets (id)")
    op.execute("ALTER TABLE liabilities ADD CONSTRAINT fk_liabilities_creditor_institution_id FOREIGN KEY (creditor_institution_id) REFERENCES financial_institutions (id)")
    op.execute("ALTER TABLE liability_payments ADD CONSTRAINT fk_liability_payments_user_id FOREIGN KEY (user_id) REFERENCES users (id)")
    op.execute("ALTER TABLE liability_payments ADD CONSTRAINT fk_liability_payments_liability_id FOREIGN KEY (liability_id) REFERENCES liabilities (id)")
    op.execute("ALTER TABLE liability_payments ADD CONSTRAINT fk_liability_payments_transaction_id FOREIGN KEY (transaction_id) REFERENCES transactions (id)")
    op.execute("ALTER TABLE liability_payments ADD CONSTRAINT fk_liability_payments_recurring_transaction_id FOREIGN KEY (recurring_transaction_id) REFERENCES recurring_transactions (id)")
    op.execute("ALTER TABLE financial_goals ADD CONSTRAINT fk_financial_goals_user_id FOREIGN KEY (user_id) REFERENCES users (id)")
    op.execute("ALTER TABLE tags ADD CONSTRAINT fk_tags_user_id FOREIGN KEY (user_id) REFERENCES users (id)")
    op.execute("ALTER TABLE transaction_tags ADD CONSTRAINT fk_transaction_tags_transaction_id FOREIGN KEY (transaction_id) REFERENCES transactions (id)")
    op.execute("ALTER TABLE transaction_tags ADD CONSTRAINT fk_transaction_tags_tag_id FOREIGN KEY (tag_id) REFERENCES tags (id)")
    op.execute("ALTER TABLE daily_financial_snapshots ADD CONSTRAINT fk_daily_financial_snapshots_user_id FOREIGN KEY (user_id) REFERENCES users (id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS daily_financial_snapshots")
    op.execute("DROP TABLE IF EXISTS transaction_tags")
    op.execute("DROP TABLE IF EXISTS tags")
    op.execute("DROP TABLE IF EXISTS financial_goals")
    op.execute("DROP TABLE IF EXISTS liability_payments")
    op.execute("DROP TABLE IF EXISTS transfers")
    op.execute("DROP TABLE IF EXISTS transactions")
    op.execute("DROP TABLE IF EXISTS recurring_transactions")
    op.execute("DROP TABLE IF EXISTS liabilities")
    op.execute("DROP TABLE IF EXISTS assets")
    op.execute("DROP TABLE IF EXISTS merchants")
    op.execute("DROP TABLE IF EXISTS categories")
    op.execute("DROP TABLE IF EXISTS accounts")
    op.execute("DROP TABLE IF EXISTS asset_types")
    op.execute("DROP TABLE IF EXISTS liability_types")
    op.execute("DROP TABLE IF EXISTS financial_institution_provider_types")
    op.execute("DROP TABLE IF EXISTS financial_institutions")
    op.execute("DROP TABLE IF EXISTS provider_types")
    op.execute("DROP TABLE IF EXISTS account_types")
    op.execute("DROP TABLE IF EXISTS users")

    op.execute("DROP TYPE IF EXISTS liability_status")
    op.execute("DROP TYPE IF EXISTS interest_type")
    op.execute("DROP TYPE IF EXISTS risk_level")
    op.execute("DROP TYPE IF EXISTS recurring_frequency")
    op.execute("DROP TYPE IF EXISTS recurring_operation_type")
    op.execute("DROP TYPE IF EXISTS transaction_type")
    op.execute("DROP TYPE IF EXISTS category_type")
