"""
Asset Service

Phase 30: Multi-Asset Support
Date: 2025-12-30

Handles multi-asset operations:
- Asset data fetching (Yahoo Finance, CoinGecko, FRED)
- Price updates
- Correlation calculations
- Asset allocation
"""

import os
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import numpy as np

from backend.database.repository import get_sync_session
from backend.database.models_assets import Asset, MultiAssetPosition, AssetCorrelation

logger = logging.getLogger(__name__)


class AssetService:
    """Multi-asset service for fetching and managing various asset classes"""

    # Asset class configurations
    ASSET_CLASSES = {
        "STOCK": {"data_source": "yahoo", "update_freq": "realtime"},
        "BOND": {"data_source": "yahoo", "update_freq": "daily"},
        "CRYPTO": {"data_source": "yahoo", "update_freq": "realtime"},  # BTC-USD, ETH-USD
        "COMMODITY": {"data_source": "yahoo", "update_freq": "daily"},  # GLD, USO
        "ETF": {"data_source": "yahoo", "update_freq": "realtime"},
        "REIT": {"data_source": "yahoo", "update_freq": "realtime"}
    }

    # Popular assets by class
    POPULAR_ASSETS = {
        "STOCK": ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
        "BOND": ["TLT", "IEF", "SHY", "LQD", "HYG"],  # ETFs for bonds
        "CRYPTO": ["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD"],
        "COMMODITY": ["GLD", "SLV", "USO", "DBA"],  # Gold, Silver, Oil, Agriculture ETFs
        "ETF": ["SPY", "QQQ", "IWM", "VTI", "VOO"],
        "REIT": ["VNQ", "IYR", "SCHH", "RWR"]
    }

    def __init__(self):
        self.logger = logger

    def get_asset_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for any asset

        Args:
            symbol: Asset symbol (AAPL, BTC-USD, GLD, etc.)

        Returns:
            Current price or None
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")

            if data.empty:
                self.logger.warning(f"No price data for {symbol}")
                return None

            return float(data['Close'].iloc[-1])

        except Exception as e:
            self.logger.error(f"Error fetching price for {symbol}: {e}")
            return None

    def get_asset_info(self, symbol: str) -> Optional[Dict]:
        """
        Get detailed asset information

        Args:
            symbol: Asset symbol

        Returns:
            Asset info dict or None
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Determine asset class
            asset_class = self._determine_asset_class(symbol, info)

            return {
                "symbol": symbol,
                "name": info.get("longName", info.get("shortName", symbol)),
                "asset_class": asset_class,
                "exchange": info.get("exchange"),
                "currency": info.get("currency", "USD"),
                "sector": info.get("sector"),  # For stocks
                "market_cap": info.get("marketCap"),
                "current_price": info.get("regularMarketPrice"),
                "description": info.get("longBusinessSummary", "")
            }

        except Exception as e:
            self.logger.error(f"Error fetching info for {symbol}: {e}")
            return None

    def _determine_asset_class(self, symbol: str, info: Dict) -> str:
        """
        Determine asset class from symbol and info

        Args:
            symbol: Asset symbol
            info: Yahoo Finance info dict

        Returns:
            Asset class string
        """
        # Crypto: ends with -USD or -USDT
        if symbol.endswith("-USD") or symbol.endswith("-USDT"):
            return "CRYPTO"

        # Bond ETFs
        bond_symbols = ["TLT", "IEF", "SHY", "LQD", "HYG", "AGG", "BND"]
        if symbol in bond_symbols:
            return "BOND"

        # Commodity ETFs
        commodity_symbols = ["GLD", "SLV", "USO", "DBA", "DBC", "PDBC"]
        if symbol in commodity_symbols:
            return "COMMODITY"

        # REIT ETFs
        reit_symbols = ["VNQ", "IYR", "SCHH", "RWR", "XLRE"]
        if symbol in reit_symbols:
            return "REIT"

        # Check if ETF
        quote_type = info.get("quoteType", "")
        if quote_type == "ETF":
            return "ETF"

        # Default to STOCK
        return "STOCK"

    def calculate_correlation(self, symbol1: str, symbol2: str, period: str = "1y") -> Optional[float]:
        """
        Calculate correlation between two assets

        Args:
            symbol1: First asset symbol
            symbol2: Second asset symbol
            period: Lookback period (30d, 90d, 1y)

        Returns:
            Correlation coefficient (-1.0 to 1.0) or None
        """
        try:
            # Download price data
            data1 = yf.download(symbol1, period=period, progress=False)
            data2 = yf.download(symbol2, period=period, progress=False)

            if data1.empty or data2.empty:
                self.logger.warning(f"Empty data for {symbol1} or {symbol2}")
                return None

            # Calculate returns
            returns1 = data1['Close'].pct_change().dropna()
            returns2 = data2['Close'].pct_change().dropna()

            # Align dates
            aligned = pd.concat([returns1, returns2], axis=1, join='inner')
            aligned.columns = ['asset1', 'asset2']

            # Calculate correlation
            corr = aligned['asset1'].corr(aligned['asset2'])

            return float(corr)

        except Exception as e:
            self.logger.error(f"Error calculating correlation: {e}")
            return None

    def create_asset(self, symbol: str) -> Optional[int]:
        """
        Create asset record in database

        Args:
            symbol: Asset symbol

        Returns:
            Created asset ID or None
        """
        try:
            # Get asset info
            info = self.get_asset_info(symbol)
            if not info:
                self.logger.error(f"Failed to get info for {symbol}")
                return None

            with get_sync_session() as session:
                # Check if asset already exists
                existing = session.query(Asset).filter(Asset.symbol == symbol).first()
                if existing:
                    self.logger.info(f"Asset {symbol} already exists (ID: {existing.id})")
                    return existing.id

                # Determine risk level based on asset class
                risk_level = self._determine_risk_level(info['asset_class'], symbol)

                # Calculate correlation to S&P 500
                sp500_corr = self.calculate_correlation(symbol, "SPY", period="1y")

                # Create asset
                asset = Asset(
                    symbol=symbol,
                    asset_class=info['asset_class'],
                    name=info['name'],
                    exchange=info.get('exchange'),
                    currency=info.get('currency', 'USD'),
                    sector=info.get('sector'),
                    risk_level=risk_level,
                    correlation_to_sp500=sp500_corr,
                    is_active=True,
                    extra_data={
                        "market_cap": info.get('market_cap'),
                        "description": info.get('description', '')[:500]  # Truncate
                    }
                )

                session.add(asset)
                session.commit()
                session.refresh(asset)

                self.logger.info(f"✅ Created asset: {symbol} (ID: {asset.id}, Class: {info['asset_class']})")
                return asset.id

        except Exception as e:
            self.logger.error(f"Error creating asset {symbol}: {e}")
            return None

    def _determine_risk_level(self, asset_class: str, symbol: str) -> str:
        """
        Determine risk level based on asset class

        Args:
            asset_class: Asset class
            symbol: Asset symbol

        Returns:
            Risk level string
        """
        risk_map = {
            "STOCK": "MEDIUM",
            "BOND": "LOW",
            "CRYPTO": "VERY_HIGH",
            "COMMODITY": "MEDIUM",
            "ETF": "LOW",
            "REIT": "MEDIUM"
        }

        # Special cases
        if symbol in ["TLT", "IEF", "SHY"]:  # Treasury bonds
            return "VERY_LOW"
        if symbol in ["HYG", "JNK"]:  # Junk bonds
            return "HIGH"
        if symbol.endswith("-USD") and symbol not in ["BTC-USD", "ETH-USD"]:  # Altcoins
            return "VERY_HIGH"

        return risk_map.get(asset_class, "MEDIUM")

    def bulk_create_popular_assets(self) -> Dict[str, int]:
        """
        Bulk create popular assets across all classes

        Returns:
            Dict mapping symbol to asset ID
        """
        results = {}
        total = 0

        for asset_class, symbols in self.POPULAR_ASSETS.items():
            self.logger.info(f"Creating {asset_class} assets: {len(symbols)} symbols")

            for symbol in symbols:
                asset_id = self.create_asset(symbol)
                if asset_id:
                    results[symbol] = asset_id
                    total += 1

        self.logger.info(f"✅ Created {total} assets across {len(self.POPULAR_ASSETS)} classes")
        return results

    def update_asset_prices(self) -> int:
        """
        Update prices for all active assets

        Returns:
            Number of assets updated
        """
        try:
            with get_sync_session() as session:
                assets = session.query(Asset).filter(Asset.is_active == True).all()

                updated_count = 0

                for asset in assets:
                    price = self.get_asset_price(asset.symbol)
                    if price:
                        # Update in metadata (we don't have a price column in Asset table)
                        if asset.extra_data is None:
                            asset.extra_data = {}

                        asset.extra_data['last_price'] = price
                        asset.extra_data['last_updated'] = datetime.now().isoformat()
                        asset.updated_at = datetime.now()

                        updated_count += 1

                session.commit()

                self.logger.info(f"✅ Updated prices for {updated_count}/{len(assets)} assets")
                return updated_count

        except Exception as e:
            self.logger.error(f"Error updating asset prices: {e}")
            return 0


def main():
    """CLI entry point for testing"""
    logging.basicConfig(level=logging.INFO)

    service = AssetService()

    print("\n" + "="*80)
    print("Asset Service - Test Run")
    print("="*80 + "\n")

    # Bulk create popular assets
    print("Creating popular assets across all classes...")
    results = service.bulk_create_popular_assets()

    print(f"\n✅ Created {len(results)} assets:")
    for asset_class, symbols in service.POPULAR_ASSETS.items():
        created = [s for s in symbols if s in results]
        print(f"  {asset_class}: {len(created)}/{len(symbols)} - {', '.join(created[:3])}")

    # Update prices
    print("\nUpdating asset prices...")
    updated = service.update_asset_prices()
    print(f"✅ Updated {updated} asset prices")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
