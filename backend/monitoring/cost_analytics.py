"""
Cost Analytics & Monitoring System.

Tracks and analyzes costs across:
1. AI API calls (Claude, OpenAI, Gemini)
2. Data fetching (Yahoo Finance, SEC, News)
3. Storage (NAS, Database)
4. Embedding generation (RAG)

Features:
- Real-time cost tracking
- Daily/monthly aggregation
- Cost breakdown by category
- Budget alerts
- Cost projection
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CostCategory(Enum):
    """Cost categories for tracking."""

    AI_CLAUDE = "ai_claude"
    AI_OPENAI = "ai_openai"
    AI_GEMINI = "ai_gemini"
    EMBEDDING = "embedding"
    DATA_FETCH = "data_fetch"
    STORAGE = "storage"
    OTHER = "other"


@dataclass
class CostMetric:
    """Single cost metric entry."""

    category: str
    subcategory: Optional[str]
    amount_usd: float
    quantity: int  # API calls, embeddings, etc.
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class CostSummary:
    """Aggregated cost summary."""

    period: str  # "daily", "weekly", "monthly"
    start_date: date
    end_date: date
    total_cost_usd: float
    by_category: Dict[str, float]
    by_subcategory: Dict[str, float]
    api_calls: int
    embeddings_generated: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["start_date"] = self.start_date.isoformat()
        data["end_date"] = self.end_date.isoformat()
        return data


class CostAnalytics:
    """
    Cost analytics and monitoring system.

    Usage:
        analytics = CostAnalytics(db_session)

        # Track cost
        await analytics.track_cost(
            category=CostCategory.AI_CLAUDE,
            subcategory="investment_decision",
            amount_usd=0.0143,
            quantity=1,
            metadata={"ticker": "AAPL", "tokens": 2000}
        )

        # Get daily summary
        summary = await analytics.get_daily_summary(date.today())

        # Get monthly costs
        monthly = await analytics.get_monthly_costs(year=2025, month=11)

        # Check budget
        alert = await analytics.check_budget_alert(daily_limit=1.0)
    """

    # Cost limits (configurable)
    DAILY_LIMIT_USD = 1.0
    MONTHLY_LIMIT_USD = 10.0

    # API pricing (as of 2025-11)
    PRICING = {
        "claude_sonnet_4.5": {
            "input": 3.0 / 1_000_000,  # $3/M tokens
            "output": 15.0 / 1_000_000,  # $15/M tokens
        },
        "claude_haiku_4": {
            "input": 0.25 / 1_000_000,  # $0.25/M tokens
            "output": 1.25 / 1_000_000,  # $1.25/M tokens
        },
        "openai_embedding": {
            "text-embedding-3-small": 0.02 / 1_000_000  # $0.02/M tokens
        },
        "gemini_flash": {
            "input": 0.075 / 1_000_000,  # $0.075/M tokens
            "output": 0.30 / 1_000_000,  # $0.30/M tokens
        },
    }

    def __init__(self, db_session: AsyncSession):
        """
        Initialize cost analytics.

        Args:
            db_session: SQLAlchemy async session
        """
        self.db = db_session

        logger.info("CostAnalytics initialized")

    async def track_cost(
        self,
        category: CostCategory,
        subcategory: Optional[str],
        amount_usd: float,
        quantity: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Track a cost event.

        Args:
            category: Cost category
            subcategory: Subcategory (e.g., "investment_decision")
            amount_usd: Cost in USD
            quantity: Number of units (API calls, embeddings, etc.)
            metadata: Additional metadata
        """
        # For now, we'll aggregate using existing tables
        # In production, create a dedicated cost_tracking table

        logger.info(
            f"Cost tracked: {category.value}/{subcategory} "
            f"${amount_usd:.5f} (qty={quantity})"
        )

        # TODO: Insert into cost_tracking table when created

    async def get_daily_summary(self, target_date: date) -> CostSummary:
        """
        Get cost summary for a specific day.

        Args:
            target_date: Target date

        Returns:
            CostSummary for the day
        """
        start_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = start_dt + timedelta(days=1)

        # Query AI analysis cache
        from backend.core.models.embedding_models import DocumentEmbedding

        # Get embedding costs
        result = await self.db.execute(
            select(
                func.sum(DocumentEmbedding.embedding_cost_usd).label("total_cost"),
                func.count(DocumentEmbedding.id).label("count"),
            ).where(
                and_(
                    DocumentEmbedding.created_at >= start_dt,
                    DocumentEmbedding.created_at < end_dt,
                )
            )
        )

        row = result.one()
        embedding_cost = float(row.total_cost or 0)
        embedding_count = int(row.count or 0)

        # TODO: Query ai_analysis_cache when available

        # Build summary
        summary = CostSummary(
            period="daily",
            start_date=target_date,
            end_date=target_date,
            total_cost_usd=embedding_cost,
            by_category={
                CostCategory.EMBEDDING.value: embedding_cost,
            },
            by_subcategory={},
            api_calls=0,
            embeddings_generated=embedding_count,
        )

        return summary

    async def get_monthly_costs(
        self, year: int, month: int
    ) -> List[CostSummary]:
        """
        Get daily cost summaries for a month.

        Args:
            year: Year
            month: Month (1-12)

        Returns:
            List of daily CostSummary
        """
        # Get first and last day of month
        first_day = date(year, month, 1)

        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)

        # Get daily summaries
        summaries = []
        current_date = first_day

        while current_date <= last_day:
            summary = await self.get_daily_summary(current_date)
            summaries.append(summary)
            current_date += timedelta(days=1)

        return summaries

    async def get_monthly_total(self, year: int, month: int) -> float:
        """
        Get total monthly cost.

        Args:
            year: Year
            month: Month

        Returns:
            Total cost in USD
        """
        summaries = await self.get_monthly_costs(year, month)
        return sum(s.total_cost_usd for s in summaries)

    async def get_cost_breakdown(
        self, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """
        Get detailed cost breakdown for a period.

        Args:
            start_date: Start date
            end_date: End date (inclusive)

        Returns:
            Cost breakdown dict
        """
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        # Query embedding costs by document type
        from backend.core.models.embedding_models import DocumentEmbedding

        result = await self.db.execute(
            select(
                DocumentEmbedding.document_type,
                func.sum(DocumentEmbedding.embedding_cost_usd).label("total_cost"),
                func.count(DocumentEmbedding.id).label("count"),
                func.sum(DocumentEmbedding.token_count).label("total_tokens"),
            )
            .where(
                and_(
                    DocumentEmbedding.created_at >= start_dt,
                    DocumentEmbedding.created_at <= end_dt,
                )
            )
            .group_by(DocumentEmbedding.document_type)
        )

        by_type = {}
        total_cost = 0.0
        total_embeddings = 0
        total_tokens = 0

        for row in result:
            doc_type = row.document_type
            cost = float(row.total_cost or 0)
            count = int(row.count or 0)
            tokens = int(row.total_tokens or 0)

            by_type[doc_type] = {
                "cost_usd": cost,
                "embeddings": count,
                "tokens": tokens,
                "avg_cost": cost / count if count > 0 else 0,
            }

            total_cost += cost
            total_embeddings += count
            total_tokens += tokens

        breakdown = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": (end_date - start_date).days + 1,
            },
            "total": {
                "cost_usd": total_cost,
                "embeddings": total_embeddings,
                "tokens": total_tokens,
            },
            "by_document_type": by_type,
            "projections": {
                "daily_avg": total_cost
                / max((end_date - start_date).days + 1, 1),
                "monthly_projected": total_cost
                / max((end_date - start_date).days + 1, 1)
                * 30,
            },
        }

        return breakdown

    async def check_budget_alert(
        self, daily_limit: Optional[float] = None, monthly_limit: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Check if costs exceed budget limits.

        Args:
            daily_limit: Daily limit in USD (default: DAILY_LIMIT_USD)
            monthly_limit: Monthly limit in USD (default: MONTHLY_LIMIT_USD)

        Returns:
            Alert dict with status and details
        """
        daily_limit = daily_limit or self.DAILY_LIMIT_USD
        monthly_limit = monthly_limit or self.MONTHLY_LIMIT_USD

        # Check today's cost
        today = date.today()
        daily_summary = await self.get_daily_summary(today)
        daily_cost = daily_summary.total_cost_usd

        # Check this month's cost
        monthly_total = await self.get_monthly_total(today.year, today.month)

        # Determine alert level
        alerts = []

        if daily_cost > daily_limit:
            alerts.append(
                {
                    "level": "CRITICAL",
                    "type": "daily_limit_exceeded",
                    "message": f"Daily cost ${daily_cost:.2f} exceeds limit ${daily_limit:.2f}",
                    "current": daily_cost,
                    "limit": daily_limit,
                    "percentage": (daily_cost / daily_limit) * 100,
                }
            )
        elif daily_cost > daily_limit * 0.8:
            alerts.append(
                {
                    "level": "WARNING",
                    "type": "daily_limit_approaching",
                    "message": f"Daily cost ${daily_cost:.2f} is 80%+ of limit ${daily_limit:.2f}",
                    "current": daily_cost,
                    "limit": daily_limit,
                    "percentage": (daily_cost / daily_limit) * 100,
                }
            )

        if monthly_total > monthly_limit:
            alerts.append(
                {
                    "level": "CRITICAL",
                    "type": "monthly_limit_exceeded",
                    "message": f"Monthly cost ${monthly_total:.2f} exceeds limit ${monthly_limit:.2f}",
                    "current": monthly_total,
                    "limit": monthly_limit,
                    "percentage": (monthly_total / monthly_limit) * 100,
                }
            )
        elif monthly_total > monthly_limit * 0.8:
            alerts.append(
                {
                    "level": "WARNING",
                    "type": "monthly_limit_approaching",
                    "message": f"Monthly cost ${monthly_total:.2f} is 80%+ of limit ${monthly_limit:.2f}",
                    "current": monthly_total,
                    "limit": monthly_limit,
                    "percentage": (monthly_total / monthly_limit) * 100,
                }
            )

        result = {
            "status": "CRITICAL" if any(a["level"] == "CRITICAL" for a in alerts) else "WARNING" if alerts else "OK",
            "daily": {
                "cost": daily_cost,
                "limit": daily_limit,
                "percentage": (daily_cost / daily_limit) * 100,
            },
            "monthly": {
                "cost": monthly_total,
                "limit": monthly_limit,
                "percentage": (monthly_total / monthly_limit) * 100,
            },
            "alerts": alerts,
            "checked_at": datetime.now().isoformat(),
        }

        if alerts:
            logger.warning(
                f"Budget alert: {result['status']} - {len(alerts)} alert(s)"
            )

        return result

    async def get_cost_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Get cost trends over the last N days.

        Args:
            days: Number of days to analyze

        Returns:
            Trend analysis dict
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        # Get daily costs
        daily_costs = []
        current_date = start_date

        while current_date <= end_date:
            summary = await self.get_daily_summary(current_date)
            daily_costs.append(
                {
                    "date": current_date.isoformat(),
                    "cost": summary.total_cost_usd,
                    "embeddings": summary.embeddings_generated,
                }
            )
            current_date += timedelta(days=1)

        # Calculate trends
        total_cost = sum(d["cost"] for d in daily_costs)
        avg_daily = total_cost / days
        max_daily = max(d["cost"] for d in daily_costs) if daily_costs else 0
        min_daily = min(d["cost"] for d in daily_costs) if daily_costs else 0

        # Calculate 7-day moving average
        ma_7 = []
        for i in range(len(daily_costs)):
            if i >= 6:
                window = daily_costs[i - 6 : i + 1]
                ma_7.append(sum(d["cost"] for d in window) / 7)
            else:
                ma_7.append(None)

        trends = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days,
            },
            "summary": {
                "total_cost": total_cost,
                "avg_daily": avg_daily,
                "max_daily": max_daily,
                "min_daily": min_daily,
            },
            "daily_costs": daily_costs,
            "moving_average_7d": ma_7,
            "projections": {
                "next_7_days": avg_daily * 7,
                "next_30_days": avg_daily * 30,
            },
        }

        return trends


# Example usage
if __name__ == "__main__":
    import asyncio
    from backend.core.database import get_db

    async def demo():
        async with get_db() as db:
            analytics = CostAnalytics(db)

            # Get today's summary
            today = date.today()
            summary = await analytics.get_daily_summary(today)
            print(f"\nToday's Summary ({today}):")
            print(f"  Total Cost: ${summary.total_cost_usd:.5f}")
            print(f"  Embeddings: {summary.embeddings_generated}")

            # Get monthly total
            monthly = await analytics.get_monthly_total(today.year, today.month)
            print(f"\nMonthly Total ({today.year}-{today.month:02d}): ${monthly:.2f}")

            # Check budget
            alert = await analytics.check_budget_alert()
            print(f"\nBudget Status: {alert['status']}")
            print(f"  Daily: ${alert['daily']['cost']:.2f} / ${alert['daily']['limit']:.2f}")
            print(f"  Monthly: ${alert['monthly']['cost']:.2f} / ${alert['monthly']['limit']:.2f}")

            # Get cost trends
            trends = await analytics.get_cost_trends(days=7)
            print(f"\n7-Day Trends:")
            print(f"  Avg Daily: ${trends['summary']['avg_daily']:.5f}")
            print(f"  30-Day Projection: ${trends['projections']['next_30_days']:.2f}")

    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo())
