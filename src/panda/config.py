from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Slack
    slack_bot_token: str
    slack_app_token: str
    slack_signing_secret: str

    # Scraping
    firecrawl_api_key: str
    jina_api_key: str = ""

    # LLM
    anthropic_api_key: str
    llm_model: str = "claude-sonnet-4-20250514"

    # Storage
    storage_path: str = "./data/output"

    # Logging
    log_level: str = "INFO"
