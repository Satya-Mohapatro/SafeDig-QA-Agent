import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    app_name: str = "AI Map QA & Validation Agent"
    environment: str = Field(default="development", validation_alias="APP_ENV")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    safe_mode: bool = Field(default=True, validation_alias="SAFE_MODE")
    max_workers: int = Field(default=4, validation_alias="MAX_WORKERS")
    default_dpi: int = Field(default=300, validation_alias="DEFAULT_DPI")
    output_dir: str = Field(default="qa_output", validation_alias="OUTPUT_DIR")
    
    # Versioning
    engine_version: str = "1.0.0"
    policy_version: str = "1.0.0"
    warning_catalogue_version: str = "1.0.0"
    legend_version: str = "1.0.0"
    agent_version: str = "1.0.0"

    # Database Configuration
    database_url: str = Field(default="sqlite+aiosqlite:///safedig.db", validation_alias="DATABASE_URL")

    # LLM & QA Agent Configuration (Advisory Only)
    enable_llm_advisory: bool = Field(default=True, validation_alias="ENABLE_LLM_ADVISORY")
    llm_endpoint: str = Field(default="http://localhost:11434", validation_alias="LLM_ENDPOINT")
    llm_model: str = Field(default="qwen2.5:latest", validation_alias="LLM_MODEL")
    llm_timeout_sec: float = Field(default=10.0, validation_alias="LLM_TIMEOUT_SEC")

settings = AppSettings()
