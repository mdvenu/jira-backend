from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_url: str = ""
    jira_enabled: bool = False
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "meeting_user"
    mysql_password: str = "meeting_password"
    mysql_database: str = "meeting_intelligence"
    jira_project_key: str = "AIM"
    default_user: str = "accountId_default"
    groq_model: str = "llama-3.1-8b-instant"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
