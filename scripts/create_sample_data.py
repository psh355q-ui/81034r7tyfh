"""
Create sample trade data for testing Advanced Analytics
"""
import asyncio
import os
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import AsyncSessionLocal
from backend.core.models.analytics_models import TradeExecution

async def create_sample_trades():
    """Create sample trade executions for testing"""
    print("Creating sample trade data...")

    async with AsyncSessionLocal() as session:
        # Sample strategies, sectors, and AI sources
        strategies = ['momentum', 'mean_reversion', 'breakout', 'trend_following']
        sectors = ['Technology', 'Healthcare', 'Finance', 'Consumer', 'Energy']
        ai_sources = ['claude', 'gemini', 'chatgpt', 'ensemble']
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA', 'META', 'AMZN', 'JPM', 'BAC', 'XOM']

        trades = []
        base_date = datetime.now() - timedelta(days=90)

        # Create 100 sample trades
        for i in range(100):
            # Random but realistic data
            import random

            ticker = random.choice(tickers)
            strategy = random.choice(strategies)
            sector = random.choice(sectors)
            ai_source = random.choice(ai_sources)

            entry_price = Decimal(str(random.uniform(50, 500)))
            exit_price = entry_price * Decimal(str(random.uniform(0.95, 1.15)))  # -5% to +15%
            shares = random.randint(10, 100)

            entry_time = base_date + timedelta(days=i, hours=random.randint(9, 15))
            exit_time = entry_time + timedelta(hours=random.randint(1, 48))

            position_size = entry_price * Decimal(shares)
            pnl = (exit_price - entry_price) * Decimal(shares)
            pnl_pct = ((exit_price - entry_price) / entry_price) * 100

            trade = TradeExecution(
                trade_id=f"TRADE_{i:04d}",
                ticker=ticker,
                action='BUY',
                signal_timestamp=entry_time - timedelta(seconds=30),
                execution_timestamp=entry_time,
                exit_timestamp=exit_time,
                signal_price=entry_price * Decimal('0.999'),
                entry_price=entry_price,
                exit_price=exit_price,
                target_price=entry_price * Decimal('1.10'),
                stop_loss_price=entry_price * Decimal('0.95'),
                shares=shares,
                position_size_usd=position_size,
                portfolio_pct=Decimal(str(random.uniform(1, 10))),
                pnl_usd=pnl,
                pnl_pct=pnl_pct,
                is_win=(pnl > 0),
                hold_duration_hours=Decimal((exit_time - entry_time).total_seconds() / 3600),
                slippage_bps=Decimal(str(random.uniform(-5, 5))),
                execution_time_ms=Decimal(str(random.uniform(50, 500))),
                commission_usd=Decimal('1.00'),
                ai_source=ai_source,
                signal_confidence=Decimal(str(random.uniform(0.6, 0.95))),
                signal_reason=f"Strong {strategy} signal detected",
                rag_documents_used=random.randint(3, 15),
                strategy_name=strategy,
                market_regime=random.choice(['bull', 'bear', 'sideways', 'volatile']),
                sector=sector,
                risk_score=Decimal(str(random.uniform(0.2, 0.8))),
                position_risk_pct=Decimal(str(random.uniform(0.5, 3.0))),
                status='CLOSED',
                exit_reason='TARGET' if pnl > 0 else 'STOP_LOSS' if pnl < -position_size * Decimal('0.03') else 'TIME_EXIT',
            )

            trades.append(trade)

        # Add all trades to session
        session.add_all(trades)
        await session.commit()

        print(f"\n✓ Created {len(trades)} sample trades")

        # Print summary
        wins = sum(1 for t in trades if t.is_win)
        total_pnl = sum(t.pnl_usd for t in trades)

        print(f"  - Win rate: {wins/len(trades)*100:.1f}%")
        print(f"  - Total PnL: ${total_pnl:,.2f}")
        print(f"  - Date range: {trades[0].execution_timestamp.date()} to {trades[-1].execution_timestamp.date()}")

        print("\n✓ Sample data created successfully!")

if __name__ == "__main__":
    # Set DATABASE_URL if not already set
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "postgresql+asyncpg://ai_trading_user:wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU@localhost:5432/ai_trading"

    asyncio.run(create_sample_trades())
