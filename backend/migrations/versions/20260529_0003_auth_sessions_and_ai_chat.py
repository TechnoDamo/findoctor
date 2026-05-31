"""auth sessions, ai chat tables, uuid defaults, role column

Revision ID: 20260529_0003
Revises: 20260529_0002
Create Date: 2026-05-29

Добавляет:
  - Таблицу auth_sessions для хранения сессий (refresh-токены, logout)
  - Таблицы ai_chat_conversations и ai_chat_messages для AI-чатов
  - DEFAULT gen_random_uuid() для всех UUID первичных ключей
  - Колонку role в таблицу users
"""

from alembic import op

revision = "20260529_0003"
down_revision = "20260529_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # Таблица сессий аутентификации
    # Хранит хеш refresh-токена, что позволяет отзывать сессии через logout.
    # При логине создаётся запись, при logout — удаляется.
    # =========================================================================
    op.execute("""
        CREATE TABLE auth_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            refresh_token_hash VARCHAR NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_auth_sessions_user_id ON auth_sessions (user_id)")
    op.execute(
        "CREATE INDEX ix_auth_sessions_token_hash ON auth_sessions (refresh_token_hash)"
    )

    # =========================================================================
    # Таблицы AI-чата
    # =========================================================================
    op.execute("""
        CREATE TABLE ai_chat_conversations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(200),
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_ai_chat_conversations_user_id ON ai_chat_conversations (user_id)")

    op.execute("""
        CREATE TABLE ai_chat_messages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            conversation_id UUID NOT NULL
                REFERENCES ai_chat_conversations(id) ON DELETE CASCADE,
            role VARCHAR NOT NULL,
            content JSONB NOT NULL DEFAULT '[]'::jsonb,
            metadata JSONB,
            created_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)
    op.execute(
        "CREATE INDEX ix_ai_chat_messages_conversation_id "
        "ON ai_chat_messages (conversation_id)"
    )

    # =========================================================================
    # DEFAULT gen_random_uuid() для всех UUID PRIMARY KEY
    # Гарантирует, что UUID генерируется на стороне БД, даже при прямых INSERT.
    # =========================================================================
    uuid_tables = [
        "users",
        "account_types",
        "provider_types",
        "financial_institutions",
        "liability_types",
        "asset_types",
        "accounts",
        "categories",
        "merchants",
        "transactions",
        "recurring_transactions",
        "transfers",
        "assets",
        "liabilities",
        "liability_payments",
        "financial_goals",
        "tags",
        "daily_financial_snapshots",
    ]
    for table in uuid_tables:
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN id SET DEFAULT gen_random_uuid()"
        )

    # =========================================================================
    # Колонка роли пользователя
    # Сейчас все пользователи — 'user', но закладываем будущее разграничение.
    # =========================================================================
    op.execute(
        "ALTER TABLE users ADD COLUMN role VARCHAR NOT NULL DEFAULT 'user'"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS role")

    uuid_tables = [
        "users",
        "account_types",
        "provider_types",
        "financial_institutions",
        "liability_types",
        "asset_types",
        "accounts",
        "categories",
        "merchants",
        "transactions",
        "recurring_transactions",
        "transfers",
        "assets",
        "liabilities",
        "liability_payments",
        "financial_goals",
        "tags",
        "daily_financial_snapshots",
    ]
    for table in uuid_tables:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN id DROP DEFAULT")

    op.execute("DROP TABLE IF EXISTS ai_chat_messages")
    op.execute("DROP TABLE IF EXISTS ai_chat_conversations")
    op.execute("DROP TABLE IF EXISTS auth_sessions")
