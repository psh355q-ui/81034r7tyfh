"""
Pydantic models for Feature Store.

Models defined here match the spec.md and plan.md data model section.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class Feature(BaseModel):
    """
    A calculated metric for a ticker at a specific timestamp.

    Examples:
        - ticker="AAPL", feature_name="ret_5d", value=0.0523, as_of_timestamp=2024-11-08
        - ticker="MSFT", feature_name="vol_20d", value=0.0234, as_of_timestamp=2024-11-08
    """

    ticker: str = Field(..., description="Stock ticker symbol (e.g., AAPL, 005930.KS)")
    feature_name: str = Field(..., description="Feature name (e.g., ret_5d, vol_20d, mom_20d)")
    value: Optional[float] = Field(None, description="Feature value (None if unavailable)")
    as_of_timestamp: datetime = Field(
        ..., description="Point-in-time timestamp (for backtesting)"
    )
    calculated_at: datetime = Field(
        default_factory=datetime.utcnow, description="When this feature was computed"
    )
    version: int = Field(default=1, description="Feature calculation logic version")
    metadata: Optional[dict] = Field(
        default=None, description="Additional context (e.g., data source, warnings)"
    )

    @validator("ticker")
    def ticker_uppercase(cls, v: str) -> str:
        """Normalize ticker to uppercase."""
        return v.upper()

    @validator("feature_name")
    def feature_name_lowercase(cls, v: str) -> str:
        """Normalize feature name to lowercase."""
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "feature_name": "ret_5d",
                "value": 0.0523,
                "as_of_timestamp": "2024-11-08T00:00:00Z",
                "calculated_at": "2024-11-08T10:30:00Z",
                "version": 1,
                "metadata": {"source": "yahoo_finance", "cache_hit": False},
            }
        }


class FeatureRequest(BaseModel):
    """
    Request model for retrieving features.

    Examples:
        - Get latest features: FeatureRequest(ticker="AAPL", feature_names=["ret_5d", "vol_20d"])
        - Get historical: FeatureRequest(ticker="AAPL", feature_names=["ret_5d"], as_of=datetime(2024, 6, 15))
    """

    ticker: str = Field(..., description="Stock ticker symbol")
    feature_names: list[str] = Field(..., description="List of feature names to retrieve")
    as_of: Optional[datetime] = Field(
        default=None, description="Point-in-time (None = latest)"
    )
    version: Optional[int] = Field(
        default=None, description="Feature version (None = latest)"
    )

    @validator("ticker")
    def ticker_uppercase(cls, v: str) -> str:
        return v.upper()

    @validator("feature_names")
    def feature_names_lowercase(cls, v: list[str]) -> list[str]:
        return [name.lower() for name in v]

    @validator("feature_names")
    def feature_names_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("feature_names cannot be empty")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "feature_names": ["ret_5d", "vol_20d", "mom_20d"],
                "as_of": None,
                "version": None,
            }
        }


class FeatureResponse(BaseModel):
    """
    Response model for feature retrieval.

    Contains requested features plus metadata about cache hits, latency, cost.
    """

    ticker: str
    features: dict[str, Optional[float]] = Field(
        ..., description="Map of feature_name -> value (None if unavailable)"
    )
    as_of: datetime = Field(..., description="Timestamp used for feature retrieval")
    cache_hits: int = Field(0, description="Number of features retrieved from cache")
    cache_misses: int = Field(0, description="Number of features computed on-the-fly")
    latency_ms: float = Field(0.0, description="Total retrieval latency in milliseconds")
    cost_usd: float = Field(0.0, description="Estimated cost for this request (API calls)")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "features": {"ret_5d": 0.0523, "vol_20d": 0.0234, "mom_20d": 0.0156},
                "as_of": "2024-11-08T00:00:00Z",
                "cache_hits": 3,
                "cache_misses": 0,
                "latency_ms": 4.2,
                "cost_usd": 0.0,
            }
        }
