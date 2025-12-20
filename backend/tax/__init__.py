"""
Tax Optimization Module
세금 최적화 관련 기능
"""

from .tax_loss_harvesting import (
    TaxLossHarvester,
    TaxBracket,
    Position,
    LossPosition,
    AlternativeStock,
    TaxHarvestingRecommendation,
    format_recommendation_report
)

__all__ = [
    "TaxLossHarvester",
    "TaxBracket",
    "Position",
    "LossPosition",
    "AlternativeStock",
    "TaxHarvestingRecommendation",
    "format_recommendation_report",
]
