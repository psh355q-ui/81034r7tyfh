"""
Asset Correlation Scheduler

Phase 32: Asset Correlation 자동 계산
Date: 2025-12-30

매일 실행되어 자산 간 상관계수를 계산:
1. 30일 상관계수 (rolling correlation)
2. 90일 상관계수
3. 1년 상관계수

Schedule: 매일 01:00 (KST) - 시장 종료 후
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import yfinance as yf
import pandas as pd
import numpy as np
from sqlalchemy import and_

from backend.database.repository import get_sync_session
from backend.database.models_assets import Asset, AssetCorrelation

logger = logging.getLogger(__name__)


class CorrelationScheduler:
    """
    자산 간 상관계수 자동 계산 스케줄러

    매일 실행되어 모든 자산 페어의 30d/90d/1y 상관계수 계산
    """

    def __init__(self):
        """Initialize scheduler"""
        self.scheduler_name = "CorrelationScheduler"

    def get_active_assets(self) -> List[Asset]:
        """
        활성화된 자산 목록 조회

        Returns:
            List of active Asset objects
        """
        logger.info("📊 Fetching active assets")

        with get_sync_session() as session:
            assets = session.query(Asset).filter(
                Asset.is_active == True
            ).order_by(Asset.symbol).all()

            logger.info(f"✅ Found {len(assets)} active assets")
            return assets

    def fetch_price_data(
        self,
        symbols: List[str],
        period: str = "1y"
    ) -> pd.DataFrame:
        """
        가격 데이터 다운로드 (yfinance)

        Args:
            symbols: 심볼 리스트
            period: 조회 기간 (30d, 90d, 1y)

        Returns:
            DataFrame with Close prices (index: Date, columns: Symbols)
        """
        logger.info(f"📥 Downloading price data for {len(symbols)} symbols (period: {period})")

        try:
            # Download data
            raw_data = yf.download(
                symbols,
                period=period,
                progress=False,
                group_by='ticker'
            )

            # Handle single vs multiple symbols
            if len(symbols) == 1:
                # Single symbol: raw_data is DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
                prices = raw_data['Close'].to_frame(name=symbols[0])
            else:
                # Multiple symbols: raw_data has MultiIndex columns (Ticker, Price)
                # Extract Close prices
                prices = pd.DataFrame()
                for symbol in symbols:
                    try:
                        if (symbol, 'Close') in raw_data.columns:
                            prices[symbol] = raw_data[(symbol, 'Close')]
                        elif 'Close' in raw_data.columns:
                            # Fallback for single symbol
                            prices[symbol] = raw_data['Close']
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to extract {symbol}: {e}")
                        continue

            # Drop NaN rows
            prices = prices.dropna()

            logger.info(f"✅ Downloaded {len(prices)} days of price data")
            return prices

        except Exception as e:
            logger.error(f"❌ Failed to download price data: {e}")
            return pd.DataFrame()

    def calculate_correlation(
        self,
        prices: pd.DataFrame,
        symbol1: str,
        symbol2: str
    ) -> Optional[float]:
        """
        두 자산 간 상관계수 계산

        Args:
            prices: Price DataFrame
            symbol1: First symbol
            symbol2: Second symbol

        Returns:
            Correlation coefficient (-1.0 to 1.0) or None
        """
        try:
            if symbol1 not in prices.columns or symbol2 not in prices.columns:
                return None

            # Calculate returns
            returns1 = prices[symbol1].pct_change().dropna()
            returns2 = prices[symbol2].pct_change().dropna()

            # Align data
            aligned = pd.concat([returns1, returns2], axis=1).dropna()

            if len(aligned) < 10:  # Need at least 10 data points
                return None

            # Calculate correlation
            corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])

            return float(corr) if not np.isnan(corr) else None

        except Exception as e:
            logger.warning(f"⚠️ Failed to calculate correlation {symbol1} vs {symbol2}: {e}")
            return None

    def calculate_all_correlations(
        self,
        assets: List[Asset]
    ) -> Dict[str, Dict[Tuple[str, str], float]]:
        """
        모든 자산 페어의 상관계수 계산 (30d, 90d, 1y)

        Args:
            assets: List of Asset objects

        Returns:
            Dict mapping period to {(symbol1, symbol2): correlation}
        """
        logger.info(f"🔢 Calculating correlations for {len(assets)} assets")

        symbols = [asset.symbol for asset in assets]
        results = {
            "30d": {},
            "90d": {},
            "1y": {}
        }

        # Download price data for each period
        periods = {
            "30d": self.fetch_price_data(symbols, period="30d"),
            "90d": self.fetch_price_data(symbols, period="90d"),
            "1y": self.fetch_price_data(symbols, period="1y")
        }

        # Calculate correlations for all pairs
        total_pairs = len(assets) * (len(assets) - 1) // 2
        calculated = 0

        for i, asset1 in enumerate(assets):
            for asset2 in assets[i + 1:]:
                symbol1 = asset1.symbol
                symbol2 = asset2.symbol

                # Calculate for each period
                for period_key, prices in periods.items():
                    if prices.empty:
                        continue

                    corr = self.calculate_correlation(prices, symbol1, symbol2)
                    if corr is not None:
                        results[period_key][(symbol1, symbol2)] = corr

                calculated += 1
                if calculated % 10 == 0:
                    logger.info(f"   Progress: {calculated}/{total_pairs} pairs")

        logger.info(f"✅ Calculated correlations:")
        for period, data in results.items():
            logger.info(f"   {period}: {len(data)} pairs")

        return results

    def save_correlations(
        self,
        correlations: Dict[str, Dict[Tuple[str, str], float]],
        asset_id_map: Dict[str, int]
    ) -> int:
        """
        상관계수를 asset_correlations 테이블에 저장

        Args:
            correlations: Correlation results by period
            asset_id_map: Map symbol to asset_id

        Returns:
            Number of records saved
        """
        logger.info("💾 Saving correlations to database")

        saved_count = 0

        with get_sync_session() as session:
            for (symbol1, symbol2) in correlations.get("1y", {}).keys():
                # Get asset IDs
                asset1_id = asset_id_map.get(symbol1)
                asset2_id = asset_id_map.get(symbol2)

                if not asset1_id or not asset2_id:
                    continue

                # Get correlations for all periods
                corr_30d = correlations.get("30d", {}).get((symbol1, symbol2))
                corr_90d = correlations.get("90d", {}).get((symbol1, symbol2))
                corr_1y = correlations.get("1y", {}).get((symbol1, symbol2))

                # Check if record exists
                existing = session.query(AssetCorrelation).filter(
                    and_(
                        AssetCorrelation.asset1_id == asset1_id,
                        AssetCorrelation.asset2_id == asset2_id
                    )
                ).first()

                if existing:
                    # Update existing record
                    existing.correlation_30d = corr_30d
                    existing.correlation_90d = corr_90d
                    existing.correlation_1y = corr_1y
                    existing.calculated_at = datetime.now()
                else:
                    # Create new record
                    correlation = AssetCorrelation(
                        asset1_id=asset1_id,
                        asset2_id=asset2_id,
                        correlation_30d=corr_30d,
                        correlation_90d=corr_90d,
                        correlation_1y=corr_1y,
                        calculated_at=datetime.now()
                    )
                    session.add(correlation)

                saved_count += 1

            session.commit()

        logger.info(f"✅ Saved {saved_count} correlation records")
        return saved_count

    def run_correlation_calculation(self) -> Dict:
        """
        상관계수 계산 사이클 실행

        1. 활성 자산 조회
        2. 가격 데이터 다운로드
        3. 상관계수 계산 (30d, 90d, 1y)
        4. DB 저장

        Returns:
            Calculation results
        """
        logger.info("🚀 Starting correlation calculation cycle")
        start_time = datetime.now()

        results = {
            "timestamp": start_time.isoformat(),
            "success": False,
            "assets_count": 0,
            "pairs_calculated": 0,
            "records_saved": 0
        }

        try:
            # Step 1: Get active assets
            assets = self.get_active_assets()
            results["assets_count"] = len(assets)

            if len(assets) < 2:
                logger.warning("⚠️ Need at least 2 assets to calculate correlations")
                return results

            # Step 2 & 3: Calculate correlations
            correlations = self.calculate_all_correlations(assets)

            # Count total pairs
            total_pairs = sum(len(data) for data in correlations.values())
            results["pairs_calculated"] = total_pairs // 3  # Each pair has 3 periods

            # Step 4: Save to database
            asset_id_map = {asset.symbol: asset.id for asset in assets}
            saved_count = self.save_correlations(correlations, asset_id_map)
            results["records_saved"] = saved_count

            # Success
            results["success"] = True
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Correlation calculation completed in {duration:.1f}s")

        except Exception as e:
            logger.error(f"❌ Correlation calculation failed: {e}", exc_info=True)
            results["error"] = str(e)

        return results


def run_scheduler():
    """Entry point for running the scheduler"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    scheduler = CorrelationScheduler()
    results = scheduler.run_correlation_calculation()

    print("\n" + "="*80)
    print("📊 CORRELATION CALCULATION RESULTS")
    print("="*80)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Success: {results['success']}")
    print(f"Assets: {results['assets_count']}")
    print(f"Pairs Calculated: {results['pairs_calculated']}")
    print(f"Records Saved: {results['records_saved']}")

    if not results['success']:
        print(f"Error: {results.get('error', 'Unknown error')}")

    print("="*80)

    return results


if __name__ == "__main__":
    run_scheduler()
