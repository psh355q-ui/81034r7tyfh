import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from backend.skills.base_skill import BaseSkill, SkillCategory, CostTier
from backend.backtesting.consensus_backtest import ConsensusBacktest
from backend.backtesting.backtest_engine import BacktestEngine

logger = logging.getLogger(__name__)

class BacktestSkill(BaseSkill):
    """
    백테스팅 및 성과 분석 Skill
    
    ConsensusBacktest Runner를 통해 시뮬레이션을 실행하고
    PerformanceAnalyzer로 분석 결과를 반환한다.
    """
    
    def __init__(self):
        super().__init__(
            name="Trading.Backtest",
            category=SkillCategory.TRADING,
            description="Run backtests for consensus strategies and analyze performance.",
            keywords=["backtest", "simulation", "performance", "history", "verify"],
            cost_tier=CostTier.LOW, # Local simulation
            requires_api_key=False
        )
        
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "run_consensus_backtest",
                    "description": "Run a consensus strategy backtest on historical data.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tickers": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of tickers to backtest (e.g., ['AAPL', 'NVDA'])"
                            },
                            "start_date": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD)"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD)"
                            },
                            "initial_capital": {
                                "type": "number",
                                "description": "Initial capital in USD",
                                "default": 100000.0
                            },
                            "consensus_threshold": {
                                "type": "number",
                                "description": "Approval threshold (0.0 to 1.0)",
                                "default": 0.6
                            }
                        },
                        "required": ["tickers", "start_date", "end_date"]
                    }
                }
            }
        ]

    async def execute(self, tool_name: str, **kwargs) -> Any:
        if tool_name == "run_consensus_backtest":
            return await self._run_consensus_backtest(**kwargs)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _run_consensus_backtest(
        self, 
        tickers: List[str], 
        start_date: str, 
        end_date: str, 
        initial_capital: float = 100000.0,
        consensus_threshold: float = 0.6
    ) -> str:
        """Execute consensus backtest"""
        try:
            # Parse dates
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            runner = ConsensusBacktest(
                initial_capital=initial_capital,
                consensus_threshold=consensus_threshold,
                use_mock_consensus=True # Default to mock for now
            )
            
            result = await runner.run(tickers, start_dt, end_dt)
            return result["summary"]
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            return f"Error running backtest: {str(e)}"
