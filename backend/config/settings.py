"""
Configuration settings for AI Trading System.
Loads from environment variables with validation.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable loading."""
    
    # ===== Database Configuration =====
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_max_connections: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")
    
    timescale_host: str = Field(default="localhost", env="TIMESCALE_HOST")
    timescale_port: int = Field(default=5432, env="TIMESCALE_PORT")
    timescale_db: str = Field(default="ai_trading", env="TIMESCALE_DB")
    timescale_user: str = Field(default="postgres", env="TIMESCALE_USER")
    timescale_password: str = Field(default="postgres", env="TIMESCALE_PASSWORD")
    timescale_min_pool_size: int = Field(default=5, env="TIMESCALE_MIN_POOL_SIZE")
    timescale_max_pool_size: int = Field(default=20, env="TIMESCALE_MAX_POOL_SIZE")
    
    @property
    def timescale_dsn(self) -> str:
        """Construct TimescaleDB connection string."""
        return (
            f"postgresql://{self.timescale_user}:{self.timescale_password}"
            f"@{self.timescale_host}:{self.timescale_port}/{self.timescale_db}"
        )
    
    # ===== AI API Keys =====
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    gemini_api_key: str = Field(default="", env="GEMINI_API_KEY")
    chatgpt_api_key: str = Field(default="", env="CHATGPT_API_KEY")
    
    # ===== AI Configuration =====
    ai_max_tokens: int = Field(default=4096, env="AI_MAX_TOKENS")
    ai_temperature: float = Field(default=0.3, env="AI_TEMPERATURE")
    ai_request_timeout: int = Field(default=30, env="AI_REQUEST_TIMEOUT")
    ai_max_retries: int = Field(default=3, env="AI_MAX_RETRIES")
    
    @validator("openai_api_key")
    def validate_openai_key(cls, v):
        """Validate OpenAI API key for RAG embeddings."""
        if not v:
            return v
        if not v.startswith("sk-"):
            raise ValueError(
                "OPENAI_API_KEY is required for RAG embeddings. "
                "Get your key at https://platform.openai.com/api-keys"
            )
        return v
    
    # ===== Trading API Keys =====
    kis_app_key: Optional[str] = Field(default=None, env="KIS_APP_KEY")
    kis_app_secret: Optional[str] = Field(default=None, env="KIS_APP_SECRET")
    kis_account_number: Optional[str] = Field(default=None, env="KIS_ACCOUNT_NUMBER")
    kis_account_product_code: str = Field(default="01", env="KIS_ACCOUNT_PRODUCT_CODE")
    
    # ===== Feature Flags =====
    enable_live_trading: bool = Field(default=False, env="ENABLE_LIVE_TRADING")
    enable_auto_tagging: bool = Field(default=True, env="ENABLE_AUTO_TAGGING")
    enable_incremental_updates: bool = Field(default=True, env="ENABLE_INCREMENTAL_UPDATES")
    
    # ===== RAG Configuration =====
    # Embedding Settings
    embedding_model: str = Field(default="text-embedding-3-small", env="EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=1536, env="EMBEDDING_DIMENSIONS")
    embedding_cost_per_million_tokens: float = Field(default=0.02, env="EMBEDDING_COST_PER_MILLION_TOKENS")
    
    # Vector Search Settings
    vector_search_min_similarity: float = Field(default=0.7, env="VECTOR_SEARCH_MIN_SIMILARITY")
    vector_search_default_top_k: int = Field(default=5, env="VECTOR_SEARCH_DEFAULT_TOP_K")
    
    # Auto-Tagging Settings
    auto_tag_use_ai: bool = Field(default=True, env="AUTO_TAG_USE_AI")
    auto_tag_claude_model: str = Field(default="claude-haiku-4-20250514", env="AUTO_TAG_CLAUDE_MODEL")
    auto_tag_max_tags: int = Field(default=20, env="AUTO_TAG_MAX_TAGS")
    
    # Incremental Update Settings
    incremental_update_enabled: bool = Field(default=True, env="INCREMENTAL_UPDATE_ENABLED")
    incremental_update_cron: str = Field(default="0 2 * * *", env="INCREMENTAL_UPDATE_CRON")
    
    # ===== Cost Limits =====
    daily_embedding_budget_usd: float = Field(default=0.10, env="DAILY_EMBEDDING_BUDGET_USD")
    monthly_embedding_budget_usd: float = Field(default=1.00, env="MONTHLY_EMBEDDING_BUDGET_USD")
    alert_on_budget_exceeded: bool = Field(default=True, env="ALERT_ON_BUDGET_EXCEEDED")
    
    # ===== Monitoring =====
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    grafana_port: int = Field(default=3000, env="GRAFANA_PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # ===== Application Settings =====
    app_env: str = Field(default="development", env="APP_ENV")
    debug: bool = Field(default=True, env="DEBUG")
    api_port: int = Field(default=8000, env="API_PORT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()


# Validation on import
def validate_settings():
    """Validate critical settings on application startup."""
    errors = []
    
    # Check OpenAI API key for embeddings
    if not settings.openai_api_key or not settings.openai_api_key.startswith("sk-"):
        errors.append(
            "❌ OPENAI_API_KEY is required for RAG embeddings\n"
            "   Get your key at: https://platform.openai.com/api-keys\n"
            "   Add to .env file: OPENAI_API_KEY=sk-proj-..."
        )
    
    # Check Anthropic API key for auto-tagging (if enabled)
    if settings.enable_auto_tagging:
        if not settings.anthropic_api_key or not settings.anthropic_api_key.startswith("sk-ant-"):
            errors.append(
                "⚠️  ANTHROPIC_API_KEY recommended for auto-tagging (optional)\n"
                "   Get your key at: https://console.anthropic.com/\n"
                "   Or disable: ENABLE_AUTO_TAGGING=false"
            )
    
    # Check database connectivity
    if not settings.timescale_host:
        errors.append("❌ TIMESCALE_HOST is required for database connection")
    
    if errors:
        print("\n🚨 Configuration Errors:\n")
        for error in errors:
            print(error)
        print("\n💡 Fix these in your .env file and restart\n")
        
        if any("❌" in e for e in errors):
            raise ValueError("Critical configuration errors found")
    
    print("✅ Configuration validated successfully")


if __name__ == "__main__":
    # Test configuration loading
    validate_settings()
    
    print(f"\n📊 Current Configuration:")
    print(f"   Environment: {settings.app_env}")
    print(f"   Database: {settings.timescale_host}:{settings.timescale_port}/{settings.timescale_db}")
    print(f"   Redis: {settings.redis_url}")
    print(f"   Embedding Model: {settings.embedding_model}")
    print(f"   Auto-Tagging: {'Enabled' if settings.enable_auto_tagging else 'Disabled'}")
    print(f"   Incremental Updates: {'Enabled' if settings.enable_incremental_updates else 'Disabled'}")
    print(f"   Daily Budget: ${settings.daily_embedding_budget_usd}")
