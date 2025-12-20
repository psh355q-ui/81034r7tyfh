"""
Korea Investment & Securities Broker Integration

Wrapper for KIS Open Trading API for real broker trading.

Features:
- Token-based authentication
- Overseas stock trading (US markets: NASDAQ, NYSE, AMEX)
- Account balance queries
- Real-time price quotes
- Order execution (market/limit orders)

Based on:
- KIS Open Trading API (D:\code\open-trading-api-main)
- Previous KIS integration (D:\code\kis_trading-main)

Author: AI Trading System Team
Date: 2025-11-15
"""

import sys
import os
import logging
from typing import Dict, List, Optional
from pathlib import Path

# Add KIS official API to path (주석 처리 - Docker에서는 사용 불가)
# KIS_API_PATH = r"D:\code\open-trading-api-main\examples_user"
# if KIS_API_PATH not in sys.path:
#     sys.path.insert(0, KIS_API_PATH)

try:
    import backend.trading.kis_client as kc
    import backend.trading.overseas_stock as osf
    KIS_AVAILABLE = True
except ImportError as e:
    KIS_AVAILABLE = False
    logging.warning(f"KIS API not available: {e}")

logger = logging.getLogger(__name__)


class KISBroker:
    """
    Korea Investment & Securities Broker Integration.

    Handles real trading with KIS Open Trading API.
    Supports overseas stocks (US markets).
    """

    def __init__(
        self,
        account_no: str,
        product_code: str = "01",
        is_virtual: bool = True,
    ):
        """
        Initialize KIS Broker.

        Args:
            account_no: KIS account number (8 digits)
            product_code: Product code (01: 종합계좌)
            is_virtual: Use virtual trading (True) or real trading (False)
        """
        if not KIS_AVAILABLE:
            raise ImportError("KIS API not available. Check KIS_API_PATH.")

        # Parse account number (CANO-PRDT format support)
        if '-' in account_no:
            self.cano, self.prdt_cd = account_no.split('-')
        else:
            self.cano = account_no
            self.prdt_cd = product_code

        self.account_no = account_no # Keep original for reference
        self.is_virtual = is_virtual

        # Server type
        self.svr = "vps" if is_virtual else "prod"
        self.env_dv = "demo" if is_virtual else "real"

        # Initialize authentication
        logger.info(f"Initializing KIS Broker ({'Virtual' if is_virtual else 'Real'} Trading)")
        self._authenticate()

        logger.info(f"KIS Broker initialized - Account: {account_no}")

    def _authenticate(self):
        """Authenticate with KIS API and get access token."""
        try:
            # Request new token
            logger.info(f"Requesting KIS token (server: {self.svr})...")
            # kis_client.py auth function usage: auth(svr: str = "vps", product: str = "01")
            success = kc.auth(svr=self.svr, product=self.prdt_cd)
            
            if not success:
                raise ValueError("Failed to obtain KIS access token")

            logger.info("KIS authentication successful")

        except Exception as e:
            logger.error(f"KIS authentication failed: {e}")
            raise

    # ========== Market Data ==========

    def get_price(self, symbol: str, exchange: str = "NASDAQ") -> Optional[Dict]:
        """
        Get current price for a symbol.

        Args:
            symbol: Stock symbol (e.g., AAPL, NVDA)
            exchange: Exchange code (NASDAQ, NYSE, AMEX)

        Returns:
            Price information dictionary or None
        """
        try:
            # Convert exchange code
            exchange_codes = {
                "NASDAQ": "NAS",
                "NYSE": "NYS",
                "AMEX": "AMS"
            }
            exc_cd = exchange_codes.get(exchange.upper(), "NAS")

            # Call KIS API
            data_list = osf.get_price(
                excd=exc_cd,
                symb=symbol.upper()
            )

            if data_list:
                row = data_list[0]
                return {
                    "symbol": symbol.upper(),
                    "name": row.get('name', row.get('item_name', symbol)),
                    "current_price": float(row.get('last', 0)),
                    "open_price": float(row.get('open', 0)),
                    "high_price": float(row.get('high', 0)),
                    "low_price": float(row.get('low', 0)),
                    "change": float(row.get('diff', row.get('prdy_vrss', 0))),
                    "change_rate": float(row.get('rate', row.get('prdy_ctrt', 0))),
                    "volume": int(row.get('tvol', row.get('acml_vol', 0))),
                    "exchange": exchange.upper(),
                }
            else:
                logger.error(f"No price data for {symbol}")
                return None

        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return None

    def get_account_balance(self) -> Optional[Dict]:
        """
        Get account balance and buying power.

        Returns:
            Account balance dictionary or None
        """
        try:
            # Call KIS API for balance
            # We use "NASD" as default context for now. KIS API requires an exchange code.
            # Ideally we should iterate if we support multiple exchanges.
            res = osf.get_balance(
                cano=self.cano,
                acnt_prdt_cd=self.prdt_cd,
                ovrs_excg_cd="NASD" 
            )
            
            output1 = res.get('output1', [])
            output2 = res.get('output2', {}) 

            if output1:
                # Parse balance information
                total_value = 0.0
                positions = []
                total_daily_pnl = 0.0

                for row in output1:
                    # Map fields based on debug output
                    symbol = row.get('ovrs_pdno', row.get('pdno', ''))
                    if symbol:
                        # Use exact field names from debug output
                        qty = float(row.get('ovrs_cblc_qty', row.get('hldg_qty', 0)))
                        if qty > 0:
                            avg_price = float(row.get('pchs_avg_pric', 0))
                            current_price = float(row.get('now_pric2', 0))
                            eval_amt = float(row.get('ovrs_stck_evlu_amt', row.get('frcr_evlu_amt2', 0)))
                            profit_loss = float(row.get('frcr_evlu_pfls_amt', 0))
                            
                            # Calculate Daily P&L
                            daily_pnl = 0.0
                            daily_return_pct = 0.0
                            
                            try:
                                # Map exchange code for Price API
                                raw_excg = row.get('ovrs_excg_cd', 'NASD')
                                price_excg_map = {
                                    "NASD": "NAS", "NYSE": "NYS", "AMEX": "AMS",
                                    "SEHK": "HKS", "SHAA": "SHS", "SZAA": "SZS",
                                    "TKSE": "TSE", "HASE": "HNX", "VNSE": "HSX"
                                }
                                price_excg = price_excg_map.get(raw_excg, "NAS")
                                
                                # Fetch Price Detail
                                price_detail = osf.get_price_detail(price_excg, symbol)
                                
                                if price_detail:
                                    # Parse Price Data
                                    last_price = float(price_detail.get('last', 0) or current_price)
                                    base_price = float(price_detail.get('base', 0) or last_price)
                                    
                                    # Using fetched last_price as current_price if available (more realtime)
                                    if last_price > 0:
                                        current_price = last_price
                                        # Recalculate eval_amt based on realtime price
                                        # eval_amt = current_price * qty
                                    
                                    if base_price > 0:
                                        diff = current_price - base_price
                                        daily_pnl = diff * qty
                                        daily_return_pct = (diff / base_price) * 100
                                        
                            except Exception as e:
                                logger.warning(f"Failed to calc daily P&L for {symbol}: {e}")
                            
                            positions.append({
                                "symbol": symbol,
                                "quantity": qty,
                                "avg_price": avg_price,
                                "current_price": current_price,
                                "eval_amount": eval_amt,
                                "profit_loss": profit_loss,
                                "daily_pnl": daily_pnl,
                                "daily_return_pct": daily_return_pct
                            })
                            total_value += eval_amt
                            total_daily_pnl += daily_pnl

                # Get Cash Balance (Present Balance)
                cash_usd = 0.0
                try:
                    cash_res = osf.get_present_balance(
                        cano=self.cano,
                        acnt_prdt_cd=self.prdt_cd
                    )
                    cash_out2 = cash_res.get('output2', [])
                    if cash_out2:
                        if isinstance(cash_out2, list) and len(cash_out2) > 0:
                            cash_item = cash_out2[0]
                        elif isinstance(cash_out2, dict):
                            cash_item = cash_out2
                        else:
                            cash_item = {}
                        
                        # frcr_dncl_amt_2: Foreign Deposit (USD)
                        cash_usd = float(cash_item.get('frcr_dncl_amt_2', 0))
                except Exception as e:
                    logger.error(f"Failed to fetch cash balance: {e}")

                return {
                    "total_value": total_value,
                    "positions": positions,
                    "cash": cash_usd,
                    "daily_pnl": total_daily_pnl
                }
            else:
                logger.warning("No balance data available")

                return {"total_value": 0, "positions": [], "cash": 0}

        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")
            return None

    # ========== Order Execution ==========

    def buy_market_order(
        self,
        symbol: str,
        quantity: int,
        exchange: str = "NASDAQ"
    ) -> Optional[Dict]:
        """
        Place a market buy order.

        Args:
            symbol: Stock symbol
            quantity: Number of shares
            exchange: Exchange code

        Returns:
            Order result dictionary or None
        """
        try:
            # Convert exchange code
            exchange_codes = {
                "NASDAQ": "NASD",
                "NYSE": "NYSE",
                "AMEX": "AMEX"
            }
            exc_cd = exchange_codes.get(exchange.upper(), "NASD")

            # Place order via KIS API
            result = osf.buy_order(
                cano=self.account_no,
                acnt_prdt_cd=self.product_code,
                excg=exc_cd,
                symb=symbol.upper(),
                qty=quantity,
                price=0,
                ord_dvsn="01" # Market? Check KIS API specs. Assuming 01 is market or handled by price=0
            )

            if result:
                logger.info(f"BUY order placed: {quantity} {symbol} @ MARKET")
                return {
                    "symbol": symbol,
                    "side": "BUY",
                    "quantity": quantity,
                    "order_type": "MARKET",
                    "status": "SUBMITTED",
                    "result": result
                }
            else:
                logger.error(f"Failed to place BUY order for {symbol}")
                return None

        except Exception as e:
            logger.error(f"Failed to execute buy order: {e}")
            return None

    def sell_market_order(
        self,
        symbol: str,
        quantity: int,
        exchange: str = "NASDAQ"
    ) -> Optional[Dict]:
        """
        Place a market sell order.

        Args:
            symbol: Stock symbol
            quantity: Number of shares
            exchange: Exchange code

        Returns:
            Order result dictionary or None
        """
        try:
            # Convert exchange code
            exchange_codes = {
                "NASDAQ": "NASD",
                "NYSE": "NYSE",
                "AMEX": "AMEX"
            }
            exc_cd = exchange_codes.get(exchange.upper(), "NASD")

            # Place sell order via KIS API
            result = osf.sell_order(
                cano=self.account_no,
                acnt_prdt_cd=self.product_code,
                excg=exc_cd,
                symb=symbol.upper(),
                qty=quantity,
                price=0,
                ord_dvsn="01"
            )

            if result:
                logger.info(f"SELL order placed: {quantity} {symbol} @ MARKET")
                return {
                    "symbol": symbol,
                    "side": "SELL",
                    "quantity": quantity,
                    "order_type": "MARKET",
                    "status": "SUBMITTED",
                    "result": result
                }
            else:
                logger.error(f"Failed to place SELL order for {symbol}")
                return None

        except Exception as e:
            logger.error(f"Failed to execute sell order: {e}")
            return None

    def buy_limit_order(
        self,
        symbol: str,
        quantity: int,
        price: float,
        exchange: str = "NASDAQ"
    ) -> Optional[Dict]:
        """
        Place a limit buy order.

        Args:
            symbol: Stock symbol
            quantity: Number of shares
            price: Limit price
            exchange: Exchange code

        Returns:
            Order result dictionary or None
        """
        try:
            exchange_codes = {
                "NASDAQ": "NASD",
                "NYSE": "NYSE",
                "AMEX": "AMEX"
            }
            exc_cd = exchange_codes.get(exchange.upper(), "NASD")

            result = osf.buy_order(
                cano=self.account_no,
                acnt_prdt_cd=self.product_code,
                excg=exc_cd,
                symb=symbol.upper(),
                qty=quantity,
                price=price,
                ord_dvsn="00" # Limit order
            )

            if result:
                logger.info(f"BUY LIMIT order placed: {quantity} {symbol} @ ${price}")
                return {
                    "symbol": symbol,
                    "side": "BUY",
                    "quantity": quantity,
                    "order_type": "LIMIT",
                    "price": price,
                    "status": "SUBMITTED",
                    "result": result
                }
            else:
                logger.error(f"Failed to place BUY LIMIT order for {symbol}")
                return None

        except Exception as e:
            logger.error(f"Failed to execute buy limit order: {e}")
            return None

    # ========== Utility Methods ==========

    def is_market_open(self, exchange: str = "NASDAQ") -> bool:
        """
        Check if market is currently open.

        Args:
            exchange: Exchange code

        Returns:
            True if market is open
        """
        # Simple implementation - can be enhanced
        from datetime import datetime, time as dt_time

        now = datetime.now()

        # US market hours: 9:30 AM - 4:00 PM ET (Mon-Fri)
        # For simplicity, assume any weekday
        if now.weekday() >= 5:  # Weekend
            return False

        # Approximate market hours (ignoring timezone conversion)
        market_open = dt_time(9, 30)
        market_close = dt_time(16, 0)
        current_time = now.time()

        return market_open <= current_time <= market_close

    def get_info(self) -> Dict:
        """Get broker information."""
        return {
            "broker": "Korea Investment & Securities",
            "account": self.account_no,
            "mode": "Virtual" if self.is_virtual else "Real",
            "server": self.svr,
            "available": KIS_AVAILABLE,
        }
