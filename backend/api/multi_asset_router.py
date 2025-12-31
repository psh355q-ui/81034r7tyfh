"""
Multi-Asset API Router

Phase 30: Multi-Asset Support
Date: 2025-12-30

Endpoints:
- GET /api/assets - List all assets (with filtering)
- GET /api/assets/:id - Get asset details
- GET /api/assets/stats - Asset statistics by class
- GET /api/assets/correlation-matrix - Correlation matrix
- GET /api/assets/risk-distribution - Risk level distribution
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from backend.database.repository import SessionLocal
from backend.database.models_assets import Asset, AssetCorrelation
from sqlalchemy import func, desc

router = APIRouter(prefix="/api/assets", tags=["Multi-Asset"])


# ============================================================================
# Helper Functions
# ============================================================================

def decimal_to_float(value):
    """Convert Decimal to float for JSON serialization"""
    if value is None:
        return None
    return float(value)


# ============================================================================
# GET /api/assets - List Assets
# ============================================================================

@router.get("")
async def get_assets(
    asset_class: Optional[str] = Query(None, description="Filter by asset class (STOCK, BOND, CRYPTO, etc.)"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH)"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Get list of assets with optional filtering

    **Query Parameters:**
    - asset_class: STOCK, BOND, CRYPTO, COMMODITY, ETF, REIT
    - risk_level: VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH
    - is_active: true/false
    - limit: 1-500 (default: 100)
    - offset: for pagination
    """
    session = SessionLocal()

    try:
        query = session.query(Asset)

        # Apply filters
        if asset_class:
            query = query.filter(Asset.asset_class == asset_class.upper())

        if risk_level:
            query = query.filter(Asset.risk_level == risk_level.upper())

        if is_active is not None:
            query = query.filter(Asset.is_active == is_active)

        # Order by symbol
        query = query.order_by(Asset.symbol)

        # Pagination
        total_count = query.count()
        assets = query.offset(offset).limit(limit).all()

        # Format response
        result = []
        for asset in assets:
            result.append({
                "id": asset.id,
                "symbol": asset.symbol,
                "asset_class": asset.asset_class,
                "name": asset.name,
                "exchange": asset.exchange,
                "currency": asset.currency,
                "sector": asset.sector,
                "bond_type": asset.bond_type,
                "crypto_type": asset.crypto_type,
                "commodity_type": asset.commodity_type,
                "risk_level": asset.risk_level,
                "correlation_to_sp500": decimal_to_float(asset.correlation_to_sp500),
                "is_active": asset.is_active,
                "created_at": asset.created_at.isoformat() if asset.created_at else None
            })

        return {
            "total": total_count,
            "count": len(result),
            "offset": offset,
            "limit": limit,
            "assets": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching assets: {str(e)}")

    finally:
        session.close()


# ============================================================================
# GET /api/assets/:id - Get Asset Details
# ============================================================================

@router.get("/{asset_id}")
async def get_asset_by_id(asset_id: int):
    """
    Get detailed information for a specific asset
    """
    session = SessionLocal()

    try:
        asset = session.query(Asset).filter(Asset.id == asset_id).first()

        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset with id {asset_id} not found")

        return {
            "id": asset.id,
            "symbol": asset.symbol,
            "asset_class": asset.asset_class,
            "name": asset.name,
            "exchange": asset.exchange,
            "currency": asset.currency,
            "sector": asset.sector,
            "bond_type": asset.bond_type,
            "maturity_date": asset.maturity_date.isoformat() if asset.maturity_date else None,
            "coupon_rate": decimal_to_float(asset.coupon_rate),
            "crypto_type": asset.crypto_type,
            "commodity_type": asset.commodity_type,
            "risk_level": asset.risk_level,
            "correlation_to_sp500": decimal_to_float(asset.correlation_to_sp500),
            "is_active": asset.is_active,
            "extra_data": asset.extra_data,
            "created_at": asset.created_at.isoformat() if asset.created_at else None,
            "updated_at": asset.updated_at.isoformat() if asset.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching asset: {str(e)}")

    finally:
        session.close()


# ============================================================================
# GET /api/assets/stats - Asset Statistics
# ============================================================================

@router.get("/stats/overview")
async def get_asset_stats():
    """
    Get asset statistics grouped by class

    Returns:
    - Count by asset class
    - Count by risk level
    - Average correlation to S&P500
    """
    session = SessionLocal()

    try:
        # Count by asset class
        class_counts = (
            session.query(
                Asset.asset_class,
                func.count(Asset.id).label('count')
            )
            .filter(Asset.is_active == True)
            .group_by(Asset.asset_class)
            .order_by(Asset.asset_class)
            .all()
        )

        by_class = {cls: count for cls, count in class_counts}

        # Count by risk level
        risk_counts = (
            session.query(
                Asset.risk_level,
                func.count(Asset.id).label('count')
            )
            .filter(Asset.is_active == True)
            .group_by(Asset.risk_level)
            .order_by(Asset.risk_level)
            .all()
        )

        by_risk = {risk: count for risk, count in risk_counts}

        # Average correlation by class
        avg_corr = (
            session.query(
                Asset.asset_class,
                func.avg(Asset.correlation_to_sp500).label('avg_correlation')
            )
            .filter(Asset.is_active == True)
            .filter(Asset.correlation_to_sp500.isnot(None))
            .group_by(Asset.asset_class)
            .order_by(Asset.asset_class)
            .all()
        )

        avg_correlation_by_class = {
            cls: decimal_to_float(corr) for cls, corr in avg_corr
        }

        # Total count
        total_assets = session.query(func.count(Asset.id)).filter(Asset.is_active == True).scalar()

        return {
            "total_assets": total_assets,
            "by_asset_class": by_class,
            "by_risk_level": by_risk,
            "avg_correlation_to_sp500": avg_correlation_by_class
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching asset stats: {str(e)}")

    finally:
        session.close()


# ============================================================================
# GET /api/assets/correlation-matrix - Correlation Matrix
# ============================================================================

@router.get("/correlation/matrix")
async def get_correlation_matrix(
    period: str = Query("90d", description="Time period: 30d, 90d, 1y")
):
    """
    Get correlation matrix for all assets

    **Query Parameters:**
    - period: 30d, 90d, 1y (default: 90d)

    **Returns:**
    - Matrix of correlations between all assets
    - List of symbols for axis labels
    """
    session = SessionLocal()

    try:
        # Determine which correlation column to use
        period_map = {
            "30d": "correlation_30d",
            "90d": "correlation_90d",
            "1y": "correlation_1y"
        }

        if period not in period_map:
            raise HTTPException(status_code=400, detail=f"Invalid period: {period}. Use 30d, 90d, or 1y")

        corr_column = period_map[period]

        # Get all active assets
        assets = session.query(Asset).filter(Asset.is_active == True).order_by(Asset.symbol).all()
        symbols = [asset.symbol for asset in assets]
        asset_ids = {asset.id: asset.symbol for asset in assets}

        # Get correlations
        correlations = session.query(AssetCorrelation).all()

        # Build correlation matrix
        matrix = {}
        for symbol in symbols:
            matrix[symbol] = {}
            for other_symbol in symbols:
                if symbol == other_symbol:
                    matrix[symbol][other_symbol] = 1.0
                else:
                    matrix[symbol][other_symbol] = None

        # Fill in correlation values
        for corr in correlations:
            symbol1 = asset_ids.get(corr.asset1_id)
            symbol2 = asset_ids.get(corr.asset2_id)

            if symbol1 and symbol2:
                # Get the appropriate correlation value
                if corr_column == "correlation_30d":
                    value = decimal_to_float(corr.correlation_30d)
                elif corr_column == "correlation_90d":
                    value = decimal_to_float(corr.correlation_90d)
                else:  # correlation_1y
                    value = decimal_to_float(corr.correlation_1y)

                if value is not None:
                    matrix[symbol1][symbol2] = value
                    matrix[symbol2][symbol1] = value  # Symmetric

        return {
            "period": period,
            "symbols": symbols,
            "matrix": matrix,
            "note": "Null values indicate correlation not yet calculated"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching correlation matrix: {str(e)}")

    finally:
        session.close()


# ============================================================================
# GET /api/assets/risk-distribution - Risk Distribution
# ============================================================================

@router.get("/risk/distribution")
async def get_risk_distribution():
    """
    Get risk level distribution with asset details

    **Returns:**
    - Count per risk level
    - List of assets in each risk level
    """
    session = SessionLocal()

    try:
        # Risk levels in order
        risk_levels = ["VERY_LOW", "LOW", "MEDIUM", "HIGH", "VERY_HIGH"]

        distribution = {}

        for risk_level in risk_levels:
            assets = (
                session.query(Asset)
                .filter(Asset.is_active == True)
                .filter(Asset.risk_level == risk_level)
                .order_by(Asset.symbol)
                .all()
            )

            distribution[risk_level] = {
                "count": len(assets),
                "assets": [
                    {
                        "symbol": asset.symbol,
                        "name": asset.name,
                        "asset_class": asset.asset_class,
                        "correlation_to_sp500": decimal_to_float(asset.correlation_to_sp500)
                    }
                    for asset in assets
                ]
            }

        return {
            "risk_levels": risk_levels,
            "distribution": distribution
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching risk distribution: {str(e)}")

    finally:
        session.close()
