
import logging
from datetime import datetime
from typing import List, Dict, Optional
import json
import asyncpg
from backend.models.trading_decision import TradingDecision
from backend.config.settings import settings

logger = logging.getLogger(__name__)

class DecisionStore:
    """
    Storage for AI Trading Decisions using TimescaleDB.
    Enables tracking of AI performance over time.
    """
    
    def __init__(self, db_pool: asyncpg.Pool = None):
        self.db = db_pool
        # If pool is not provided, it should be set later or obtained from global pool
        
    async def initialize_table(self):
        """Create trading_decisions table if not exists"""
        if not self.db:
            return

        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS trading_decisions (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                ticker TEXT NOT NULL,
                action TEXT NOT NULL,
                conviction FLOAT NOT NULL,
                price_at_analysis FLOAT,
                target_price FLOAT,
                stop_loss FLOAT,
                reasoning TEXT,
                model_version TEXT,
                structured_data JSONB,
                
                -- Performance tracking (updated later)
                actual_return_1d FLOAT,
                actual_return_5d FLOAT,
                is_correct BOOLEAN
            );
            
            -- Convert to hypertable for time-series efficiency
            SELECT create_hypertable('trading_decisions', 'timestamp', if_not_exists => TRUE);
            
            CREATE INDEX IF NOT EXISTS idx_decisions_ticker ON trading_decisions(ticker, timestamp DESC);
        """)
        logger.info("Initialized trading_decisions table")

    async def save_decision(self, decision: TradingDecision, current_price: float = None) -> int:
        """
        Save a trading decision to the database.
        
        Returns:
            int: The ID of the inserted record
        """
        if not self.db:
            logger.error("DB pool not initialized in DecisionStore")
            return -1

        try:
            # Convert decision to dict for JSONB storage
            decision_dict = decision.to_dict()
            
            row_id = await self.db.fetchval("""
                INSERT INTO trading_decisions (
                    timestamp, ticker, action, conviction, 
                    price_at_analysis, target_price, stop_loss, 
                    reasoning, model_version, structured_data
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
            """,
                datetime.fromisoformat(decision_dict['timestamp']) if isinstance(decision_dict['timestamp'], str) else decision.timestamp,
                decision.ticker,
                decision.action,
                decision.conviction,
                current_price,
                decision.target_price,
                decision.stop_loss,
                decision.reasoning,
                decision.model_version,
                json.dumps(decision_dict)
            )
            
            logger.info(f"Saved decision for {decision.ticker} (ID: {row_id})")
            return row_id
            
        except Exception as e:
            logger.error(f"Failed to save decision: {e}")
            return -1

    async def get_latest_decision(self, ticker: str) -> Optional[Dict]:
        """Get the most recent decision for a ticker"""
        if not self.db:
            return None
            
        row = await self.db.fetchrow("""
            SELECT * FROM trading_decisions 
            WHERE ticker = $1 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, ticker)
        
        if row:
            return dict(row)
        return None

    async def get_history(self, ticker: str, limit: int = 10) -> List[Dict]:
        """Get decision history for a ticker"""
        if not self.db:
            return []

        rows = await self.db.fetch("""
            SELECT * FROM trading_decisions 
            WHERE ticker = $1 
            ORDER BY timestamp DESC 
            LIMIT $2
        """, ticker, limit)

        return [dict(row) for row in rows]

    async def get_all_history(self, limit: int = 50, ticker: Optional[str] = None) -> List[Dict]:
        """Get recent decision history (global or ticker specific)"""
        if not self.db:
            return []

        if ticker:
            rows = await self.db.fetch("""
                SELECT * FROM trading_decisions 
                WHERE ticker = $1 
                ORDER BY timestamp DESC 
                LIMIT $2
            """, ticker.upper(), limit)
        else:
            rows = await self.db.fetch("""
                SELECT * FROM trading_decisions 
                ORDER BY timestamp DESC 
                LIMIT $1
            """, limit)

        # Parse structured_data if available to return full context
        results = []
        for row in rows:
            data = dict(row)
            if data.get('structured_data'):
                try:
                    # Merge structured data but prefer row values if conflict (row values are indexes)
                    struct = json.loads(data['structured_data'])
                    data.update(struct)
                except:
                    pass
            results.append(data)
            
        return results
