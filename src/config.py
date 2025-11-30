"""
Configuration management for AnalysisChain
Handles environment variables, model settings, and system parameters
"""

from pathlib import Path
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Keys
    anthropic_api_key: str = Field(default="", description="Claude API key")
    google_api_key: str = Field(default="", description="Google Gemini API key")
    
    # Default Provider
    default_provider: Literal["claude", "gemini"] = Field(
        default="claude",
        description="Default LLM provider"
    )
    
    # Claude Settings
    claude_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Claude model name"
    )
    claude_max_tokens: int = Field(default=8192, ge=1, le=200000)
    claude_cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    
    # Gemini Settings
    gemini_model: str = Field(
        default="gemini-2.0-flash-exp",
        description="Gemini model name"
    )
    gemini_max_tokens: int = Field(default=8192, ge=1, le=2000000)
    gemini_cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    
    # Vector Database Settings
    vector_db_path: Path = Field(
        default=Path("./data/vectordb"),
        description="Vector database storage path"
    )
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence transformer model"
    )
    chunk_size: int = Field(default=1000, ge=100, le=10000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)
    
    # Session Settings
    session_storage_path: Path = Field(
        default=Path("./data/sessions"),
        description="Session storage path"
    )
    max_session_age: int = Field(
        default=86400,
        description="Maximum session age in seconds (24h)"
    )
    
    # Logging
    log_level: str = Field(default="INFO")
    log_file: Path = Field(default=Path("./logs/agent.log"))
    
    def model_post_init(self, __context) -> None:
        """Create necessary directories after initialization"""
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        self.session_storage_path.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
