"""
Shadow Trading Runner

Orchestrates the full pipeline (Data -> GNN -> Fusion -> RL) in "Shadow Mode".
Logs decisions and virtual execution results without sending real orders.
M4: The Face
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from backend.fusion.engine import FusionEngine, TradingIntent
from backend.fusion.normalizer import BaseSignal, SignalNormalizer

logger = logging.getLogger(__name__)

class ShadowRunner:
    """
    Runs the trading system in shadow mode.
    """
    def __init__(
        self,
        gnn_builder: Any,
        fusion_engine: FusionEngine,
        rl_agent: Any,
        log_file: str = "shadow_trades.log"
    ):
        self.gnn_builder = gnn_builder
        self.fusion_engine = fusion_engine
        self.rl_agent = rl_agent
        self.log_file = log_file
        self.normalizer = SignalNormalizer()
        
    async def run_tick(self, ticker: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single tick cycle for a ticker.
        """
        # 1. Gather & Normalize Signals
        signals = []
        
        # 1.1 News Signal (Mock or Real)
        if "news" in data and data["news"]:
            # In real system, we would parse sentiment
            # Here assuming data contains 'news_score'
            news_score = data.get("news_score", 0.0)
            signals.append(
                self.normalizer.create_signal("NEWS", news_score, 0.9, {"ticker": ticker})
            )
            
        # 1.2 Price/Technical Signal
        if "price_score" in data:
             signals.append(
                self.normalizer.create_signal("CHART", data["price_score"], 0.8, {"ticker": ticker})
            )
            
        # 1.3 GNN Signal (Future integration)
        # edges = self.gnn_builder.extract_edges(...)
        
        # 2. Fusion (The Brain)
        # Mocking market state with volume if present
        market_state = {"volume": data.get("volume", 100000)}
        intent = self.fusion_engine.fuse(signals, market_state=market_state)
        
        # 3. Decision & Execution (The Hands)
        result = {
            "timestamp": datetime.now().isoformat(),
            "ticker": ticker,
            "intent": intent,
            "status": "SKIPPED",
            "execution": None
        }
        
        if intent.direction in ["BUY", "SELL"]:
            # Call RL Agent for "Virtual Execution"
            # State generation would happen here
            # For MVP shadow runner, we just ask agent for action
            
            # Mock observation
            obs = [0.0, 0.0, 0.0, 0.0] 
            action = self.rl_agent.predict(obs) # 0=Hold, 1=Limit, 2=Market
            
            execution_log = {
                "action": action,
                "price": data.get("price", 100.0),
                "virtual_fill": True if action > 0 else False
            }
            
            result["status"] = "SHADOW_FILLED" if action > 0 else "SHADOW_HOLD"
            result["execution"] = execution_log
            
        self._log_result(result)
        return result

    def _log_result(self, result: Dict):
        """Log result to file (JSONL style)."""
        # In real impl, append to file
        logger.info(f"Shadow Trade: {result}")
