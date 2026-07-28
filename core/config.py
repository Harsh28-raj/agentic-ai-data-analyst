"""
Configuration Settings for DataMind AI using Pydantic Settings.
"""
import os
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Preload .env file into environment
load_dotenv()


class Settings(BaseSettings):
    """Application Configuration Settings."""

    # Groq Cloud API Configuration
    GROQ_API_KEY: str = "your_groq_api_key_here"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    MODEL_NAME: str = "llama-3.3-70b-versatile"

    # Application Settings
    LOG_LEVEL: str = "INFO"
    MAX_FILE_SIZE_MB: int = 50
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    
    # LangSmith / LangChain Tracing
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "datamind-ai"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# Ensure fallback if GROQ_API_KEY is an empty string
if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.strip() == "":
    settings.GROQ_API_KEY = os.getenv("OPENAI_API_KEY") or "your_groq_api_key_here"

# Sync OPENAI and GROQ env vars for complete SDK compatibility
os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY
os.environ["OPENAI_API_KEY"] = settings.GROQ_API_KEY
os.environ["GROQ_BASE_URL"] = settings.GROQ_BASE_URL
os.environ["OPENAI_BASE_URL"] = settings.GROQ_BASE_URL


