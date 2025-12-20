
import logging
from datetime import datetime
from typing import List, Dict, Optional
import json
import asyncpg
from backend.ai.reasoning.models import DeepReasoningResult
from backend.config.settings import settings

logger = logging.getLogger(__name__)

class DeepReasoningStore:
    """
    Storage for Deep Reasoning Results.
    """
    
    def __init__(self, db_pool: asyncpg.Pool = None):
        self.db = db_pool

    async def initialize_table(self):
        """Create deep_reasoning_results table if not exists"""
        if not self.db:
            return

        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS deep_reasoning_results (
                id SERIAL PRIMARY KEY,
                analyzed_at TIMESTAMPTZ NOT NULL,
                news_text TEXT NOT NULL,
                theme TEXT,
                primary_ticker TEXT,
                primary_action TEXT,
                confidence FLOAT,
                result_json JSONB,
                model_used TEXT
            );
        """)
        
        try:
            await self.db.execute("""
                SELECT create_hypertable('deep_reasoning_results', 'analyzed_at', if_not_exists => TRUE);
            """)
        except Exception as e:
            logger.warning(f"Could not create hypertable (TimescaleDB might be missing): {e}")

        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_dr_ticker ON deep_reasoning_results(primary_ticker, analyzed_at DESC);
        """)
        logger.info("Initialized deep_reasoning_results table")

    async def save_result(self, result: DeepReasoningResult) -> int:
        """Save deep reasoning result to database"""
        if not self.db:
            return -1

        try:
            result_dict = result.to_dict()
            
            # Extract primary beneficiary info
            primary_ticker = None
            primary_action = None
            confidence = 0.0
            
            if result.primary_beneficiary:
                primary_ticker = result.primary_beneficiary.get('ticker')
                primary_action = result.primary_beneficiary.get('action')
                confidence = result.primary_beneficiary.get('confidence', 0.0)

            row_id = await self.db.fetchval("""
                INSERT INTO deep_reasoning_results (
                    analyzed_at, news_text, theme, 
                    primary_ticker, primary_action, confidence,
                    result_json, model_used
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """,
                datetime.fromisoformat(result_dict['analyzed_at']) if isinstance(result_dict['analyzed_at'], str) else result.analyzed_at,
                result.news_text,
                result.theme,
                primary_ticker,
                primary_action,
                confidence,
                json.dumps(result_dict),
                result.model_used
            )
            
            logger.info(f"Saved deep reasoning result (ID: {row_id})")
            return row_id
            
        except Exception as e:
            logger.error(f"Failed to save deep reasoning result: {e}")
            return -1

    async def get_history(self, limit: int = 50, ticker: Optional[str] = None) -> List[Dict]:
        """Get deep reasoning history"""
        if not self.db:
            return []

        try:
            if ticker:
                rows = await self.db.fetch("""
                    SELECT * FROM deep_reasoning_results 
                    WHERE primary_ticker = $1 
                    ORDER BY analyzed_at DESC 
                    LIMIT $2
                """, ticker.upper(), limit)
            else:
                rows = await self.db.fetch("""
                    SELECT * FROM deep_reasoning_results 
                    ORDER BY analyzed_at DESC 
                    LIMIT $1
                """, limit)

            results = []
            for row in rows:
                data = dict(row)
                if data.get('result_json'):
                    try:
                        struct = json.loads(data['result_json'])
                        data.update(struct)
                    except:
                        pass
                results.append(data)
                
            return results
        except Exception as e:
            logger.error(f"Failed to get deep reasoning history: {e}")
            return []
