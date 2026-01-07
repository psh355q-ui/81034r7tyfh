
"""
Tax Optimizer (Korean Market Special)
=====================================
Optimizes stock sales to maximize the annual capital gains tax deduction (2.5 million KRW) 
for South Korean investors trading foreign stocks.

Logic:
1. Calculate unrealized gains per position.
2. Identify positions where selling would contribute to the 2.5m KRW limit.
3. Recommend sell quantities to hit the target gain without exceeding it significantly.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal

class TaxOptimizer:
    def __init__(self, fx_rate_krw: float = 1450.0):
        """
        Args:
            fx_rate_krw: USD to KRW exchange rate (default: 1450)
        """
        self.fx_rate = Decimal(str(fx_rate_krw))
        self.annual_deduction_limit_krw = Decimal("2500000")

    def optimize_sales(self, portfolio: List[Dict[str, Any]], realized_gain_ytd_krw: float = 0.0) -> Dict[str, Any]:
        """
        Recommend sales to maximize tax deduction.
        
        Args:
            portfolio: List of positions. Each dict must have:
                - symbol (str)
                - quantity (int)
                - average_price (float)
                - current_price (float)
            realized_gain_ytd_krw: Already realized gains this year in KRW.
            
        Returns:
            Dict containing recommendations.
        """
        recommendations = []
        remaining_deduction = self.annual_deduction_limit_krw - Decimal(str(realized_gain_ytd_krw))
        
        if remaining_deduction <= 0:
            return {
                "status": "LIMIT_REACHED",
                "message": "Annual tax deduction limit already used.",
                "remaining_deduction": 0,
                "recommendations": []
            }
            
        total_potential_gain_krw = Decimal("0")
        
        # Sort positions by highest profit per share (to use limit efficiently)
        # Or maybe sort by highest % gain? Let's stick to simple unrealized gain per share.
        
        analyzed_positions = []
        for pos in portfolio:
            qty = pos['quantity']
            avg_price = Decimal(str(pos['average_price']))
            cur_price = Decimal(str(pos['current_price']))
            
            gain_per_share_usd = cur_price - avg_price
            gain_per_share_krw = gain_per_share_usd * self.fx_rate
            
            if gain_per_share_krw > 0:
                analyzed_positions.append({
                    "symbol": pos['symbol'],
                    "gain_per_share": gain_per_share_krw,
                    "max_qty": qty,
                    "current_price": cur_price
                })

        # Greedily select shares to fill the bucket
        analyzed_positions.sort(key=lambda x: x['gain_per_share'], reverse=True)
        
        current_fill = Decimal("0")
        
        for pos in analyzed_positions:
            if current_fill >= remaining_deduction:
                break
                
            # Calculate how many shares to sell
            needed_gain = remaining_deduction - current_fill
            shares_to_sell = int(needed_gain // pos['gain_per_share'])
            
            # Cap at available quantity
            shares_to_sell = min(shares_to_sell, pos['max_qty'])
            
            # If even 1 share exceeds limit too much, we might skip or take 1 if we want to fill up?
            # Strategy: It's okay to slightly exceed if it's just 1 share, but generally we stay under or maximize.
            # Let's simple floor logic: sell what fits.
            # However, if we sold 0 shares because gain per share > remaining, we might want to partial sell?
            # But stocks are discrete.
            
            # Actually, usually people want to fill exactly 2.5m.
            # If gain per share is 1m, and 2.5m left, sell 2. (Total 2m).
            # If gain per share is 3m, sell 0 (or 1 if user wants to realize anyway).
            # We stick to "Safe Fill" (do not exceed limit massively).
            
            if shares_to_sell > 0:
                realized = shares_to_sell * pos['gain_per_share']
                current_fill += realized
                recommendations.append({
                    "symbol": pos['symbol'],
                    "action": "SELL",
                    "quantity": shares_to_sell,
                    "estimated_gain_krw": float(realized),
                    "reason": "Tax Harvesting (2.5m KRW Limit)"
                })
                
        return {
            "status": "OPTIMIZED",
            "remaining_deduction_before": float(remaining_deduction),
            "expected_total_gain_krw": float(current_fill),
            "remaining_deduction_after": float(remaining_deduction - current_fill),
            "recommendations": recommendations
        }

