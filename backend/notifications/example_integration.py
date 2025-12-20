"""
Example: Integrating Telegram Notifications with AI Trading System

This file shows how to integrate the notification system with:
1. TradingAgent - Real-time trade alerts
2. Paper Trading - Execution notifications
3. Backtest Engine - Performance reports
4. System monitoring - Health checks

Author: AI Trading System
Date: 2025-11-15
"""

import asyncio
import logging
from datetime import datetime, time
from typing import Optional

# Import your existing modules
# from trading_agent import TradingAgent
# from paper_trader import PaperTrader
# from backtest_engine_full import BacktestEngine

from telegram_notifier import TelegramNotifier
from notification_manager import NotificationManager, NotificationScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== Configuration ====================

class TelegramConfig:
    """
    Telegram configuration settings.
    Add these to your .env file or config.py
    """
    # Bot credentials (get from @BotFather)
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
    CHAT_ID = "YOUR_CHAT_ID_HERE"
    
    # Notification preferences
    ENABLED = True
    NOTIFY_ON_BUY = True
    NOTIFY_ON_SELL = True
    NOTIFY_ON_HOLD = False  # Usually don't need HOLD notifications
    NOTIFY_ON_RISK = True
    NOTIFY_ON_EXECUTION = True
    
    # Scheduled reports
    DAILY_REPORT_TIME = time(21, 0)  # 9 PM
    WEEKLY_REPORT_DAY = 4  # Friday (0=Monday)


# ==================== Integration Examples ====================

class TradingAgentWithNotifications:
    """
    Example: TradingAgent with integrated Telegram notifications
    """
    
    def __init__(
        self,
        trading_agent,  # Your existing TradingAgent
        notification_manager: NotificationManager,
    ):
        self.agent = trading_agent
        self.notifier = notification_manager
    
    async def analyze_with_notifications(
        self,
        ticker: str,
        current_price: Optional[float] = None,
    ):
        """
        Analyze stock and send notification based on decision.
        """
        try:
            # Get trading decision from AI
            decision = await self.agent.analyze(ticker)
            
            # Send notification
            await self.notifier.on_trading_decision(
                decision=decision,
                current_price=current_price,
            )
            
            # If risk was detected, send additional alert
            features = getattr(decision, 'features_used', {})
            risk_score = features.get('non_standard_risk', 0.0)
            
            if risk_score >= 0.3:
                await self.notifier.on_risk_detected(
                    ticker=ticker,
                    risk_type="non_standard_risk",
                    risk_score=risk_score,
                    risk_factors=decision.risk_factors,
                    action_taken=f"Decision: {decision.action} with conviction {decision.conviction:.1%}",
                )
            
            return decision
            
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
            await self.notifier.on_system_error(
                error_type="Analysis Error",
                error_message=f"Failed to analyze {ticker}: {str(e)}",
            )
            raise


class PaperTraderWithNotifications:
    """
    Example: PaperTrader with execution notifications
    """
    
    def __init__(
        self,
        paper_trader,  # Your existing PaperTrader
        notification_manager: NotificationManager,
    ):
        self.trader = paper_trader
        self.notifier = notification_manager
        
        # Track daily P&L for reports
        self.start_of_day_value = None
        self.trades_today = 0
    
    async def execute_order(
        self,
        ticker: str,
        side: str,
        quantity: int,
        algorithm: str = "MARKET",
    ):
        """
        Execute order and send notification.
        """
        try:
            # Execute through paper trader
            result = await self.trader.execute(
                ticker=ticker,
                side=side,
                quantity=quantity,
                algorithm=algorithm,
            )
            
            self.trades_today += 1
            
            # Send execution notification
            await self.notifier.on_order_executed(
                ticker=ticker,
                side=side,
                quantity=result['quantity'],
                avg_price=result['avg_price'],
                total_value=result['total_value'],
                algorithm=algorithm,
                slippage_bps=result.get('slippage_bps'),
                commission=result.get('commission'),
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Order execution failed: {e}")
            await self.notifier.on_system_error(
                error_type="Execution Error",
                error_message=f"Failed to execute {side} {quantity} {ticker}: {str(e)}",
            )
            raise
    
    async def send_daily_report(self):
        """
        Send end-of-day portfolio report.
        """
        portfolio = await self.trader.get_portfolio_snapshot()
        
        # Calculate daily P&L
        if self.start_of_day_value:
            daily_pnl = portfolio['total_value'] - self.start_of_day_value
            daily_pnl_pct = (daily_pnl / self.start_of_day_value) * 100
        else:
            daily_pnl = 0
            daily_pnl_pct = 0
        
        await self.notifier.send_daily_portfolio_report({
            "value": portfolio['total_value'],
            "daily_pnl": daily_pnl,
            "daily_pnl_pct": daily_pnl_pct,
            "total_return_pct": portfolio.get('total_return_pct', 0),
            "positions": portfolio.get('positions', []),
            "cash": portfolio.get('cash', 0),
            "trades_today": self.trades_today,
        })
        
        # Reset for next day
        self.start_of_day_value = portfolio['total_value']
        self.trades_today = 0


# ==================== Full System Example ====================

class AITradingSystemWithNotifications:
    """
    Complete integration example showing full trading loop with notifications.
    """
    
    def __init__(self):
        # Initialize Telegram
        self.notifier = NotificationManager(
            bot_token=TelegramConfig.BOT_TOKEN,
            chat_id=TelegramConfig.CHAT_ID,
            enabled=TelegramConfig.ENABLED,
            notify_on_buy=TelegramConfig.NOTIFY_ON_BUY,
            notify_on_sell=TelegramConfig.NOTIFY_ON_SELL,
            notify_on_hold=TelegramConfig.NOTIFY_ON_HOLD,
            notify_on_risk=TelegramConfig.NOTIFY_ON_RISK,
            notify_on_execution=TelegramConfig.NOTIFY_ON_EXECUTION,
        )
        
        # Initialize your existing components
        # self.agent = TradingAgent()
        # self.paper_trader = PaperTrader()
        # self.backtest = BacktestEngine()
        
        # Wrap with notifications
        # self.agent_notified = TradingAgentWithNotifications(self.agent, self.notifier)
        # self.trader_notified = PaperTraderWithNotifications(self.paper_trader, self.notifier)
        
        # Kill switch tracking
        self.kill_switch_active = False
        self.daily_start_value = 100000
    
    async def startup(self):
        """
        System startup with notification.
        """
        await self.notifier.on_system_startup(
            version="1.0.0",
            mode="Paper Trading",
        )
        logger.info("System started with Telegram notifications")
    
    async def analyze_watchlist(self, tickers: list):
        """
        Analyze multiple stocks and send relevant notifications.
        """
        logger.info(f"Analyzing {len(tickers)} stocks...")
        
        results = {
            "buy_signals": [],
            "sell_signals": [],
            "hold_signals": [],
            "risks_detected": [],
        }
        
        for ticker in tickers:
            try:
                # Simulate analysis (replace with actual agent call)
                decision = await self._mock_analyze(ticker)
                
                # Record result
                if decision['action'] == "BUY":
                    results["buy_signals"].append(ticker)
                elif decision['action'] == "SELL":
                    results["sell_signals"].append(ticker)
                else:
                    results["hold_signals"].append(ticker)
                
                # Send notification for actionable signals
                if decision['action'] in ["BUY", "SELL"]:
                    await self.notifier.telegram.send_trade_signal(
                        ticker=ticker,
                        action=decision['action'],
                        conviction=decision['conviction'],
                        reasoning=decision['reasoning'],
                        target_price=decision.get('target_price'),
                        stop_loss=decision.get('stop_loss'),
                        position_size=decision.get('position_size'),
                        current_price=decision.get('current_price'),
                    )
                
                # Check for high risk
                if decision.get('risk_score', 0) >= 0.3:
                    results["risks_detected"].append(ticker)
                    await self.notifier.on_risk_detected(
                        ticker=ticker,
                        risk_type="PRE_CHECK",
                        risk_score=decision['risk_score'],
                        risk_factors=decision.get('risk_factors', []),
                        action_taken=f"Filtered: {decision['action']}",
                    )
                
                # Small delay to avoid rate limits
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error analyzing {ticker}: {e}")
        
        logger.info(f"Analysis complete. BUY: {len(results['buy_signals'])}, "
                   f"SELL: {len(results['sell_signals'])}, "
                   f"HOLD: {len(results['hold_signals'])}")
        
        return results
    
    async def _mock_analyze(self, ticker: str):
        """
        Mock analysis for demonstration.
        Replace with actual TradingAgent.analyze() call.
        """
        import random
        
        actions = ["BUY", "SELL", "HOLD", "HOLD", "HOLD"]
        action = random.choice(actions)
        
        return {
            "action": action,
            "conviction": random.uniform(0.5, 0.95),
            "reasoning": f"Mock analysis for {ticker}. AI determined {action} based on technical and fundamental factors.",
            "target_price": random.uniform(100, 200) if action == "BUY" else None,
            "stop_loss": random.uniform(80, 95) if action == "BUY" else None,
            "position_size": random.uniform(2, 5) if action == "BUY" else None,
            "current_price": random.uniform(95, 110),
            "risk_score": random.uniform(0, 0.8),
            "risk_factors": ["Market volatility", "Sector rotation"] if random.random() > 0.7 else [],
        }
    
    async def check_kill_switch(self, current_value: float):
        """
        Check if kill switch should be activated.
        """
        if self.kill_switch_active:
            return
        
        daily_pnl_pct = ((current_value - self.daily_start_value) / self.daily_start_value) * 100
        
        # Example: Kill switch at -2%
        threshold = -2.0
        
        if daily_pnl_pct <= threshold:
            self.kill_switch_active = True
            
            await self.notifier.on_kill_switch_activated(
                reason="Daily loss limit exceeded",
                daily_loss_pct=daily_pnl_pct,
                threshold_pct=threshold,
            )
            
            logger.critical(f"KILL SWITCH ACTIVATED! Daily P&L: {daily_pnl_pct:.2f}%")
    
    async def shutdown(self):
        """
        Clean shutdown with notification.
        """
        await self.notifier.close()
        logger.info("System shutdown complete")


# ==================== Main Runner ====================

async def main():
    """
    Example main loop with Telegram integration.
    """
    print("="*50)
    print("AI Trading System with Telegram Notifications")
    print("="*50)
    
    # Check configuration
    if TelegramConfig.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("\n⚠️  Please configure your Telegram bot credentials!")
        print("\n1. Get bot token from @BotFather")
        print("2. Update TelegramConfig.BOT_TOKEN")
        print("3. Update TelegramConfig.CHAT_ID")
        print("\nSee the README for detailed setup instructions.")
        return
    
    # Initialize system
    system = AITradingSystemWithNotifications()
    
    try:
        # Startup notification
        await system.startup()
        
        # Example: Analyze some stocks
        watchlist = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
        results = await system.analyze_watchlist(watchlist)
        
        print(f"\nAnalysis Results:")
        print(f"  BUY signals: {results['buy_signals']}")
        print(f"  SELL signals: {results['sell_signals']}")
        print(f"  HOLD signals: {results['hold_signals']}")
        print(f"  Risks detected: {results['risks_detected']}")
        
        # Check kill switch (example)
        await system.check_kill_switch(current_value=99000)  # -1% loss
        
        print("\n✅ Check your Telegram for notifications!")
        
    finally:
        await system.shutdown()


if __name__ == "__main__":
    print("\n📱 Telegram Integration Example")
    print("=" * 50)
    print("\nBefore running:")
    print("1. Create bot via @BotFather")
    print("2. Get your chat ID")
    print("3. Update credentials in this file")
    print("\nThen run: python example_integration.py")
    
    # Uncomment to run:
    # asyncio.run(main())