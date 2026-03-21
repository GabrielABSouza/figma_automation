from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # LLM — Gemini (primary)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3-flash-preview"
    gemini_temperature: float = 0.1
    gemini_max_output_tokens: int = 8192
    gemini_max_retries: int = 2

    # Figma
    figma_access_token: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://localhost:5432/figma_automation"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # App
    app_env: str = "development"
    log_level: str = "INFO"


settings = Settings()
