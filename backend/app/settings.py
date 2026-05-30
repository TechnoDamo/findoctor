"""
Настройки приложения.

Все параметры читаются из переменных окружения (файл `.env`).
Используется pydantic-settings для валидации значений на старте приложения.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Все настройки приложения FinDoctor."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Окружение приложения
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"

    # База данных
    postgres_host: str = "localhost"
    postgres_port: int = 5433
    postgres_db: str = "findoctor"
    postgres_user: str = "findoctor"
    postgres_password: str = "change_me"
    database_url: str = ""

    # JWT
    jwt_secret_key: str = "change_me_in_production"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30

    # Пароли
    bcrypt_rounds: int = 12

    # OpenAI
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_text_model: str = "gpt-4o"
    openai_audio_model: str = "gpt-4o-audio-preview"

    # AI Chat providers (OpenAI-compatible)
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""
    stt_api_key: str = ""
    stt_base_url: str = ""
    stt_model: str = ""
    tts_api_key: str = ""
    tts_base_url: str = ""
    tts_model: str = ""
    tts_voice: str = "echo"

    # Логирование
    log_level: str = "INFO"
    graylog_enabled: bool = False
    graylog_required: bool = False
    graylog_protocol: str = "udp"
    graylog_host: str = "localhost"
    graylog_port: int = 12201
    graylog_facility: str = "findoctor-backend"
    log_http_headers: bool = True
    log_http_bodies: bool = True
    log_response_headers: bool = True
    log_response_bodies: bool = True
    log_db_writes: bool = True

    @property
    def effective_database_url(self) -> str:
        """Возвращает URL БД для Alembic/SQLAlchemy (формат postgresql+psycopg://)."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def psycopg_dsn(self) -> str:
        """Возвращает строку подключения для psycopg (формат postgres://)."""
        return (
            f"postgres://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        """Возвращает список разрешённых origins для CORS."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def access_token_ttl_seconds(self) -> int:
        """Время жизни access-токена в секундах."""
        return self.access_token_ttl_minutes * 60

    @property
    def refresh_token_ttl_seconds(self) -> int:
        """Время жизни refresh-токена в секундах."""
        return self.refresh_token_ttl_days * 86400


settings = Settings()
