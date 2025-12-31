"""
Correlation API Router

Phase 32: Asset Correlation 자동 계산
Date: 2025-12-30

Endpoints:
- POST /api/correlation/calculate - 상관계수 계산 트리거
- GET /api/correlation/status - 계산 상태 조회
- GET /api/correlation/heatmap - Heatmap 데이터
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from backend.database.repository import SessionLocal
from backend.database.models_assets import Asset, AssetCorrelation
from backend.schedulers.correlation_scheduler import CorrelationScheduler

router = APIRouter(prefix="/api/correlation", tags=["Correlation"])


# ============================================================================
# Helper Functions
# ============================================================================

def decimal_to_float(value):
    """Convert Decimal to float for JSON serialization"""
    if value is None:
        return None
    return float(value)


# ============================================================================
# POST /api/correlation/calculate - Trigger Calculation
# ============================================================================

@router.post("/calculate")
async def calculate_correlations():
    """
    상관계수 계산 수동 트리거

    모든 활성 자산 간 상관계수를 계산하고 저장합니다.
    - 30일 상관계수
    - 90일 상관계수
    - 1년 상관계수

    **Returns**:
    - timestamp: 실행 시각
    - success: 성공 여부
    - assets_count: 자산 수
    - pairs_calculated: 계산된 페어 수
    - records_saved: 저장된 레코드 수
    """
    try:
        scheduler = CorrelationScheduler()
        results = scheduler.run_correlation_calculation()

        return {
            "timestamp": results["timestamp"],
            "success": results["success"],
            "assets_count": results["assets_count"],
            "pairs_calculated": results["pairs_calculated"],
            "records_saved": results["records_saved"],
            "message": "Correlation calculation completed successfully" if results["success"] else f"Calculation failed: {results.get('error', 'Unknown error')}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate correlations: {str(e)}")


# ============================================================================
# GET /api/correlation/status - Get Calculation Status
# ============================================================================

@router.get("/status")
async def get_correlation_status():
    """
    상관계수 계산 상태 조회

    **Returns**:
    - total_pairs: 총 상관계수 페어 수
    - last_calculated: 마지막 계산 시각
    - coverage: 계산 완료율
    """
    session = SessionLocal()

    try:
        # Count total correlation records
        total_pairs = session.query(AssetCorrelation).count()

        # Get last calculated time
        latest = session.query(AssetCorrelation).order_by(
            AssetCorrelation.calculated_at.desc()
        ).first()

        last_calculated = latest.calculated_at.isoformat() if latest else None

        # Count active assets
        active_assets = session.query(Asset).filter(Asset.is_active == True).count()
        expected_pairs = active_assets * (active_assets - 1) // 2

        coverage = (total_pairs / expected_pairs * 100) if expected_pairs > 0 else 0

        return {
            "total_pairs": total_pairs,
            "expected_pairs": expected_pairs,
            "coverage": round(coverage, 1),
            "last_calculated": last_calculated,
            "active_assets": active_assets
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get correlation status: {str(e)}")

    finally:
        session.close()


# ============================================================================
# GET /api/correlation/heatmap - Get Heatmap Data
# ============================================================================

@router.get("/heatmap")
async def get_correlation_heatmap(
    period: str = Query("90d", description="Time period: 30d, 90d, 1y"),
    min_correlation: Optional[float] = Query(None, ge=-1.0, le=1.0, description="Minimum correlation threshold")
):
    """
    Correlation Heatmap 데이터 조회

    **Query Parameters**:
    - period: 30d, 90d, 1y (기본 90d)
    - min_correlation: 최소 상관계수 필터 (optional)

    **Returns**:
    - symbols: 심볼 리스트 (정렬됨)
    - matrix: 상관계수 매트릭스
    - period: 조회 기간
    - generated_at: 데이터 생성 시각
    """
    session = SessionLocal()

    try:
        # Validate period
        period_map = {
            "30d": "correlation_30d",
            "90d": "correlation_90d",
            "1y": "correlation_1y"
        }

        if period not in period_map:
            raise HTTPException(status_code=400, detail=f"Invalid period: {period}. Use 30d, 90d, or 1y")

        corr_column = period_map[period]

        # Get active assets
        assets = session.query(Asset).filter(Asset.is_active == True).order_by(Asset.symbol).all()
        symbols = [asset.symbol for asset in assets]
        asset_id_to_symbol = {asset.id: asset.symbol for asset in assets}

        # Initialize matrix
        matrix = {}
        for symbol in symbols:
            matrix[symbol] = {}
            for other_symbol in symbols:
                if symbol == other_symbol:
                    matrix[symbol][other_symbol] = 1.0
                else:
                    matrix[symbol][other_symbol] = None

        # Get correlations
        correlations = session.query(AssetCorrelation).all()

        # Fill matrix
        for corr in correlations:
            symbol1 = asset_id_to_symbol.get(corr.asset1_id)
            symbol2 = asset_id_to_symbol.get(corr.asset2_id)

            if symbol1 and symbol2:
                # Get correlation value for the specified period
                if corr_column == "correlation_30d":
                    value = decimal_to_float(corr.correlation_30d)
                elif corr_column == "correlation_90d":
                    value = decimal_to_float(corr.correlation_90d)
                else:  # correlation_1y
                    value = decimal_to_float(corr.correlation_1y)

                # Apply filter if specified
                if min_correlation is not None and value is not None:
                    if abs(value) < abs(min_correlation):
                        continue

                if value is not None:
                    matrix[symbol1][symbol2] = value
                    matrix[symbol2][symbol1] = value  # Symmetric

        # Convert matrix to list format for frontend
        heatmap_data = []
        for i, symbol1 in enumerate(symbols):
            for j, symbol2 in enumerate(symbols):
                corr_value = matrix[symbol1][symbol2]
                if corr_value is not None:
                    heatmap_data.append({
                        "x": symbol1,
                        "y": symbol2,
                        "value": corr_value
                    })

        return {
            "period": period,
            "symbols": symbols,
            "matrix": matrix,
            "heatmap_data": heatmap_data,
            "generated_at": datetime.now().isoformat(),
            "note": "Null values indicate correlation not yet calculated"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get heatmap data: {str(e)}")

    finally:
        session.close()


# ============================================================================
# GET /api/correlation/pairs - Get Top Correlated Pairs
# ============================================================================

@router.get("/pairs")
async def get_top_correlated_pairs(
    period: str = Query("90d", description="Time period: 30d, 90d, 1y"),
    limit: int = Query(20, ge=1, le=100, description="Number of pairs to return"),
    sort_by: str = Query("highest", description="Sort by: highest, lowest")
):
    """
    상관계수가 높은/낮은 자산 페어 조회

    **Query Parameters**:
    - period: 30d, 90d, 1y
    - limit: 결과 수 (1-100)
    - sort_by: highest (양의 상관계수), lowest (음의 상관계수)

    **Returns**:
    - pairs: Top correlated asset pairs
    """
    session = SessionLocal()

    try:
        # Validate period
        period_map = {
            "30d": "correlation_30d",
            "90d": "correlation_90d",
            "1y": "correlation_1y"
        }

        if period not in period_map:
            raise HTTPException(status_code=400, detail=f"Invalid period: {period}")

        corr_column_name = period_map[period]

        # Get correlations
        correlations = session.query(AssetCorrelation).order_by(
            getattr(AssetCorrelation, corr_column_name).desc() if sort_by == "highest"
            else getattr(AssetCorrelation, corr_column_name).asc()
        ).limit(limit).all()

        # Get asset symbols
        asset_ids = set()
        for corr in correlations:
            asset_ids.add(corr.asset1_id)
            asset_ids.add(corr.asset2_id)

        assets = session.query(Asset).filter(Asset.id.in_(asset_ids)).all()
        asset_map = {asset.id: asset.symbol for asset in assets}

        # Format results
        pairs = []
        for corr in correlations:
            symbol1 = asset_map.get(corr.asset1_id)
            symbol2 = asset_map.get(corr.asset2_id)

            if symbol1 and symbol2:
                if corr_column_name == "correlation_30d":
                    value = decimal_to_float(corr.correlation_30d)
                elif corr_column_name == "correlation_90d":
                    value = decimal_to_float(corr.correlation_90d)
                else:
                    value = decimal_to_float(corr.correlation_1y)

                if value is not None:
                    pairs.append({
                        "symbol1": symbol1,
                        "symbol2": symbol2,
                        "correlation": value,
                        "calculated_at": corr.calculated_at.isoformat() if corr.calculated_at else None
                    })

        return {
            "period": period,
            "sort_by": sort_by,
            "count": len(pairs),
            "pairs": pairs
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get correlated pairs: {str(e)}")

    finally:
        session.close()
