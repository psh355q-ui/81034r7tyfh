"""
Configuration settings for AI Trading System

Updated for Phase 4, Task 7: Non-Standard Risk Integration
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    AI Trading System Configuration (Constitution Rules)
    
    Phase 4, Task 7 additions:
    - Non-standard risk thresholds (CRITICAL, HIGH, MODERATE)
    - Position scaling for risk levels
    """
    
    # ==================== API Keys ====================
    claude_api_key: str = Field(
        default="",
        description="Anthropic Claude API key"
    )
    
    # ==================== AI Models ====================
    claude_model: str = Field(
        default="claude-3-5-haiku-20241022",
        description="Claude model for trading decisions"
    )
    
    claude_temperature: float = Field(
        default=0.3,
        description="Temperature for Claude (0=deterministic, 1=creative)"
    )
    
    # ==================== Pre-Check Thresholds ====================
    max_volatility_pct: float = Field(
        default=50.0,
        description="Maximum 20-day volatility (%) to pass pre-check"
    )
    
    min_momentum_pct: float = Field(
        default=-30.0,
        description="Minimum 20-day momentum (%) to pass pre-check"
    )
    
    # ==================== Post-Check Thresholds ====================
    conviction_threshold_buy: float = Field(
        default=0.7,
        description="Minimum conviction for BUY (0-1)"
    )
    
    conviction_threshold_sell: float = Field(
        default=0.6,
        description="Minimum conviction for SELL (0-1)"
    )
    
    # ==================== Risk Management ====================
    max_position_size_pct: float = Field(
        default=5.0,
        description="Maximum position size as % of portfolio"
    )
    
    stop_loss_fixed_pct: float = Field(
        default=3.0,
        description="Fixed stop-loss percentage"
    )
    
    kill_switch_daily_loss_pct: float = Field(
        default=2.0,
        description="Daily loss % that triggers kill switch"
    )
    
    # ==================== Management Credibility (Phase 4, Task 2) ====================
    min_management_credibility: float = Field(
        default=0.3,
        description="Minimum management credibility score to pass pre-check (0-1)"
    )
    
    management_credibility_position_scaling: bool = Field(
        default=True,
        description="Enable position size reduction for medium credibility stocks"
    )
    
    # ==================== Supply Chain Risk ====================
    min_supply_chain_risk_threshold: float = Field(
        default=0.6,
        description="Maximum acceptable supply chain risk score (0-1)"
    )
    
    # ==================== Non-Standard Risk (Phase 4, Task 1) ====================
    
    # Pre-Check: CRITICAL risk threshold
    max_non_standard_risk_critical: float = Field(
        default=0.6,
        description="CRITICAL risk threshold - immediate HOLD (0-1 scale)"
    )
    
    # Post-Check: HIGH risk threshold
    max_non_standard_risk_high: float = Field(
        default=0.3,
        description="HIGH risk threshold - reduce position (0-1 scale)"
    )
    
    non_standard_risk_position_scaling: bool = Field(
        default=True,
        description="Enable position size reduction for HIGH risk stocks"
    )
    
    high_risk_position_reduction_pct: float = Field(
        default=50.0,
        description="Position reduction % for HIGH risk stocks (0-100)"
    )
    
    # ==================== Redis Cache ====================
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    redis_ttl_seconds: int = Field(
        default=300,
        description="Default TTL for Redis cache (seconds)"
    )
    
    # ==================== TimescaleDB ====================
    timescale_host: str = Field(default="localhost")
    timescale_port: int = Field(default=5432)
    timescale_user: str = Field(default="postgres")
    timescale_password: str = Field(default="")
    timescale_database: str = Field(default="ai_trading")
    
    # ==================== Feature Store ====================
    feature_store_cache_enabled: bool = Field(
        default=True,
        description="Enable Feature Store caching"
    )
    
    # ==================== News Collection (Phase 4, Task 1) ====================
    newsapi_key: str = Field(
        default="",
        description="NewsAPI.org API key (optional, 100 requests/day free tier)"
    )
    
    news_cache_ttl_hours: int = Field(
        default=1,
        description="Cache TTL for news data (hours)"
    )
    
    news_max_age_days: int = Field(
        default=7,
        description="Maximum age of news to fetch (days)"
    )

    # ==================== Telegram Notifications ====================
    telegram_bot_token: str = Field(
        default="",
        description="Telegram Bot API token from @BotFather"
    )

    telegram_chat_id: str = Field(
        default="",
        description="Telegram chat ID (user or group)"
    )

    telegram_enabled: bool = Field(
        default=False,
        description="Enable/disable Telegram notifications"
    )

    telegram_notify_on_buy: bool = Field(
        default=True,
        description="Send notification on BUY signals"
    )

    telegram_notify_on_sell: bool = Field(
        default=True,
        description="Send notification on SELL signals"
    )

    telegram_notify_on_hold: bool = Field(
        default=False,
        description="Send notification on HOLD signals"
    )

    telegram_notify_on_risk: bool = Field(
        default=True,
        description="Send notification on risk alerts"
    )

    telegram_daily_report_hour: int = Field(
        default=21,
        description="Hour to send daily report (0-23, Korea time)"
    )

    telegram_rate_limit_per_minute: int = Field(
        default=20,
        description="Maximum messages per minute to send"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
_settings = None


def get_settings() -> Settings:
    """Get global settings instance (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings