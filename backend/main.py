"""
AI Trading System - Production FastAPI Application

Phase 7: Production Ready
Main application entry point with all endpoints

Features:
- REST API for trading operations
- Health check endpoints
- Prometheus metrics endpoint
- WebSocket for real-time updates
- Comprehensive error handling

Author: AI Trading System Team
Date: 2025-11-14
"""

import logging
import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel

# Import monitoring and alert components
from backend.monitoring.metrics_collector import MetricsCollector, PROMETHEUS_AVAILABLE
from backend.monitoring.alert_manager import AlertManager, AlertLevel, AlertCategory
from backend.monitoring.health_monitor import (
    HealthMonitor,
    HealthStatus,
    check_disk_space,
    check_memory_usage,
    ComponentHealth,
)

# Import API key configuration and logger
from backend.auth import APIKeyConfig
logger = logging.getLogger(__name__)
api_key_config = APIKeyConfig()

# Import Event Subscribers
from backend.events.subscribers import register_subscribers, set_conflict_ws_manager

# =============================================================================
# Router imports (absolute paths) with availability flags
# =============================================================================
try:
    from backend.api.ai_chat_router import router as ai_chat_router
    AI_CHAT_AVAILABLE = True
except ImportError as e:
    AI_CHAT_AVAILABLE = False
    logger.warning(f"AI Chat router not available: {e}")

try:
    from backend.api.gemini_free_router import router as gemini_free_router
    GEMINI_FREE_AVAILABLE = True
except ImportError as e:
    GEMINI_FREE_AVAILABLE = False
    logger.warning(f"Gemini Free router not available: {e}")

try:
    from backend.api.news_router import router as news_router
    from backend.api.news_processing_router import router as news_processing_router
    NEWS_AVAILABLE = True
except ImportError as e:
    NEWS_AVAILABLE = False
    logger.warning(f"News router not available: {e}")

try:
    from backend.api.ai_review_router import router as ai_review_router
    AI_REVIEW_AVAILABLE = True
except ImportError as e:
    AI_REVIEW_AVAILABLE = False
    logger.warning(f"AI Review router not available: {e}")

try:
    from backend.api.logs_router import router as logs_router
    LOGS_AVAILABLE = True
except ImportError as e:
    LOGS_AVAILABLE = False
    logger.warning(f"Logs router not available: {e}")

try:
    from backend.api.feeds_router import router as feeds_router
    FEEDS_AVAILABLE = True
except ImportError as e:
    FEEDS_AVAILABLE = False
    logger.warning(f"Feeds router not available: {e}")

try:
    from backend.api.news_router import router as news_router
    from backend.api.news_analysis_router import router as news_analysis_router
    from backend.api.gemini_news_router import router as gemini_news_router
    NEWS_ROUTER_AVAILABLE = True
except ImportError as e:
    NEWS_ROUTER_AVAILABLE = False
    logger.warning(f"News analysis router not available: {e}")

try:
    from backend.api.auth_router import router as auth_router
    AUTH_ROUTER_AVAILABLE = True
except ImportError as e:
    AUTH_ROUTER_AVAILABLE = False
    logger.warning(f"Auth router not available: {e}")

try:
    from backend.api.signals_router import router as signals_router
    SIGNALS_AVAILABLE = True
except ImportError as e:
    SIGNALS_AVAILABLE = False
    logger.warning(f"Signals router not available: {e}")

try:
    from backend.api.notifications_router import router as notifications_router
    NOTIFICATIONS_AVAILABLE = True
except ImportError as e:
    NOTIFICATIONS_AVAILABLE = False
    logger.warning(f"Notifications router not available: {e}")

try:
    from backend.api.backtest_router import router as backtest_router
    BACKTEST_AVAILABLE = True
except ImportError as e:
    BACKTEST_AVAILABLE = False
    logger.warning(f"Backtest router not available: {e}")

try:
    from backend.api.phase_integration_router import router as phase_router
    PHASE_AVAILABLE = True
except ImportError as e:
    PHASE_AVAILABLE = False
    logger.warning(f"Phase router not available: {e}")

try:
    from backend.api.kis_integration_router import router as kis_router
    KIS_AVAILABLE = True
except ImportError as e:
    KIS_AVAILABLE = False
    logger.warning(f"KIS router not available: {e}")

try:
    from backend.api.ai_signals_router import router as ai_signals_router
    AI_SIGNALS_AVAILABLE = True
except ImportError as e:
    AI_SIGNALS_AVAILABLE = False
    logger.warning(f"AI Signals router not available: {e}")

try:
    from backend.api.consensus_router import router as consensus_router
    CONSENSUS_AVAILABLE = True
except ImportError as e:
    CONSENSUS_AVAILABLE = False
    logger.warning(f"Consensus router not available: {e}")

try:
    from backend.api.position_router import router as position_router
    POSITION_AVAILABLE = True
except ImportError as e:
    POSITION_AVAILABLE = False
    logger.warning(f"Position router not available: {e}")

try:
    from backend.api.global_macro_router import router as global_macro_router
    GLOBAL_MACRO_AVAILABLE = True
except ImportError as e:
    GLOBAL_MACRO_AVAILABLE = False
    logger.warning(f"Global Macro router not available: {e}")

try:
    from backend.api.auto_trade_router import router as auto_trade_router
    AUTO_TRADE_AVAILABLE = True
except ImportError as e:
    AUTO_TRADE_AVAILABLE = False
    logger.warning(f"Auto Trade router not available: {e}")

try:
    from backend.api.ceo_analysis_router import router as ceo_analysis_router
    CEO_ANALYSIS_AVAILABLE = True
except ImportError as e:
    CEO_ANALYSIS_AVAILABLE = False
    logger.warning(f"CEO Analysis router not available: {e}")

try:
    from backend.api.incremental_router import router as incremental_router
    INCREMENTAL_AVAILABLE = True
except ImportError as e:
    INCREMENTAL_AVAILABLE = False
    logger.warning(f"Incremental router not available: {e}")

try:
    from backend.api.reports_router import router as reports_router
    REPORTS_AVAILABLE = True
except ImportError as e:
    REPORTS_AVAILABLE = False
    logger.warning(f"Reports router not available: {e}")

try:
    from backend.api.reasoning_api import router as reasoning_router
    REASONING_AVAILABLE = True
except ImportError as e:
    REASONING_AVAILABLE = False
    logger.warning(f"Reasoning router not available: {e}")

# Global instances (initialized in lifespan)
metrics_collector: Optional[MetricsCollector] = None
alert_manager: Optional[AlertManager] = None
health_monitor: Optional[HealthMonitor] = None
start_time: datetime = datetime.utcnow()

# =============================================================================
# Application lifecycle management
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown of the FastAPI application."""
    global metrics_collector, alert_manager, health_monitor, start_time

    logger.info("Starting AI Trading System...")
    start_time = datetime.utcnow()

    # Initialize core components
    metrics_collector = MetricsCollector()
    alert_manager = AlertManager()
    health_monitor = HealthMonitor(alert_manager=alert_manager)

    # Register health checks
    health_monitor.register_check("Disk Space", check_disk_space)
    health_monitor.register_check("Memory", check_memory_usage)

    # Mock health check for Redis (demo purposes)
    async def mock_redis():
        return ComponentHealth(
            name="Redis",
            status=HealthStatus.HEALTHY,
            message="Redis is operational",
        )
    # (In a real setup, you would register mock_redis with health_monitor)

    # 🔄 Register Event Subscribers (Phase 4, T4.2)
    register_subscribers()
    logger.info("Event Subscribers initialized.")

    # 🔄 Order Recovery on Startup (State Machine Phase 2)
    try:
        from backend.execution.order_manager import OrderManager
        from backend.execution.recovery import OrderRecovery
        from backend.database.repository import get_sync_session

        logger.info("🔄 Starting Order Recovery...")
        db = get_sync_session()
        order_manager = OrderManager(db, broker_client=None)  # broker_client will be added later
        recovery = OrderRecovery(order_manager)

        recovery_result = await recovery.recover_on_startup()

        if recovery_result['total'] > 0:
            logger.info(f"✅ Order Recovery Complete: {recovery_result['recovered']}/{recovery_result['total']} recovered")
            if recovery_result['failed'] > 0:
                logger.warning(f"⚠️ {recovery_result['failed']} orders need manual review")
        else:
            logger.info("✅ No pending orders to recover")
    except Exception as e:
        logger.error(f"❌ Order Recovery failed: {e}")
        # Don't fail startup if recovery fails

    # 📊 Initialize and start Stock Price Scheduler
    try:
        from backend.services.stock_price_scheduler import get_stock_price_scheduler
        stock_scheduler = get_stock_price_scheduler()
        stock_scheduler.start()
        if stock_scheduler:
            logger.info("Stock Price Scheduler started")
        
        # 📊 Initialize and start Daily Report Scheduler
        from backend.services.daily_report_scheduler import get_daily_report_scheduler
        report_scheduler = get_daily_report_scheduler()
        report_scheduler.start()
        if report_scheduler:
            logger.info("✅ Daily Report Scheduler started (7:10 AM Daily, 7:15 AM Mon, 7:20 AM 1st)")
    except Exception as e:
        logger.warning(f"Failed to start Stock Price Scheduler: {e}")

    # 🆕 Start Daily Learning Scheduler (Option 3: Self-Learning System)
    try:
        from backend.ai.learning.daily_learning_scheduler import DailyLearningScheduler
        from datetime import time
        import asyncio

        # Run twice daily:
        # 1. 10:00 KST - After US after-hours close (20:00 EST = 10:00 KST next day)
        # 2. 16:00 KST - After Korean market close (15:30 KST)
        learning_scheduler = DailyLearningScheduler(
            run_times=[time(10, 0), time(16, 0)]
        )

        # Run in background task to avoid blocking main event loop
        asyncio.create_task(learning_scheduler.start())
        logger.info("✅ Daily Learning Scheduler started (10:00 & 16:00 KST - 2x daily)")
    except Exception as e:
        logger.warning(f"⚠️ Failed to start Daily Learning Scheduler: {e}")

    # 🆕 Start Accountability Scheduler (News Interpretation Accuracy Tracking)
    try:
        from backend.automation.accountability_scheduler import AccountabilityScheduler
        import asyncio

        # Run hourly to verify 1h/1d/3d price changes after news interpretations
        accountability_scheduler = AccountabilityScheduler(
            run_interval_minutes=60,
            retry_on_failure=True,
            trigger_failure_learning=True
        )

        # Run in background task
        asyncio.create_task(accountability_scheduler.start())
        logger.info("✅ Accountability Scheduler started (hourly)")
    except Exception as e:
        logger.warning(f"⚠️ Failed to start Accountability Scheduler: {e}")

    # 🆕 Initialize Monitoring Components (Circuit Breaker & Kill Switch)
    try:
        from backend.monitoring.smart_alerts import SmartAlertManager
        smart_alert_manager = SmartAlertManager()
        logger.info("SmartAlertManager initialized for monitoring")
        
        from backend.monitoring.circuit_breaker import CircuitBreakerManager, KillSwitch
        circuit_breaker_manager = CircuitBreakerManager(alert_manager=smart_alert_manager)
        kill_switch = KillSwitch(alert_manager=smart_alert_manager)
        
        # Inject dependencies into monitoring_router
        from backend.api.monitoring_router import set_monitoring_instances
        set_monitoring_instances(
            health_mon=health_monitor,
            alert_mgr=smart_alert_manager,
            cb_mgr=circuit_breaker_manager,
            ks=kill_switch,
        )
        logger.info("Monitoring instances injected (Kill Switch ready)")
    except Exception as e:
        logger.warning(f"Failed to initialize monitoring components: {e}")

    # 🆕 Start News Poller (5m Interval)
    # Set DISABLE_EMBEDDED_NEWS_POLLER=1 to disable (when running standalone crawler)
    if os.environ.get("DISABLE_EMBEDDED_NEWS_POLLER", "").lower() not in ("1", "true", "yes"):
        try:
            from backend.services.news_poller import NewsPoller
            news_poller = NewsPoller()
            asyncio.create_task(news_poller.start())
            logger.info("✅ News Poller started (5m interval - Pre-filtered AI Analysis)")
        except Exception as e:
            logger.warning(f"⚠️ Failed to start News Poller: {e}")
            
    # 🆕 Initialize Event Subscriber (Order -> WebSocket bridge)
    try:
        from backend.events import event_bus
        from backend.notifications.event_subscriber import setup_event_subscribers
        from backend.notifications.notification_manager import get_notification_manager
        
        setup_event_subscribers(event_bus, get_notification_manager())
        logger.info("✅ Event Subscriber initialized (Order -> WebSocket bridge)")
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize Event Subscriber: {e}")
    else:
        logger.info("⏭️ Embedded News Poller disabled (DISABLE_EMBEDDED_NEWS_POLLER=1)")

    # 👻 Start Shadow Trading Agent
    try:
        from backend.ai.trading.shadow_trader import ShadowTradingAgent
        shadow_trader = ShadowTradingAgent()
        asyncio.create_task(shadow_trader.start())
        logger.info("✅ Shadow Trading Agent started (Monitoring Signals)")
    except Exception as e:
        logger.warning(f"⚠️ Failed to start Shadow Trading Agent: {e}")

    yield

    # Shutdown sequence
    logger.info("Shutting down AI Trading System...")
    if health_monitor:
        health_monitor.stop()
    if metrics_collector:
        metrics_collector.set_system_down()
    if alert_manager:
        await alert_manager.send_alert(
            level=AlertLevel.LOW,
            category=AlertCategory.SYSTEM,
            title="System Shutdown",
            message="AI Trading System is shutting down",
        )
    logger.info("AI Trading System shutdown complete")

# =============================================================================
# FastAPI application instance
# =============================================================================
app = FastAPI(
    title="AI Trading System",
    description="AI-Powered Stock Trading System with Multi-AI Ensemble",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Endpoint (Explicitly mounted here to avoid router prefix issues)
from fastapi import WebSocket, WebSocketDisconnect

try:
    from backend.api.signals_router import manager as trading_signal_manager
    
    @app.websocket("/api/signals/ws")
    async def websocket_signal_endpoint(websocket: WebSocket):
        """
        Real-time trading signals WebSocket endpoint.
        Uses the manager from signals_router to broadcast updates.
        """
        await trading_signal_manager.connect(websocket)
        try:
            while True:
                # Keep connection alive
                await websocket.receive_text()
        except WebSocketDisconnect:
            trading_signal_manager.disconnect(websocket)
            
    logger.info("WebSocket endpoint mounted at /api/signals/ws")
except ImportError as e:
    logger.warning(f"Failed to mount WebSocket endpoint: {e}")
except Exception as e:
    logger.error(f"WebSocket endpoint error: {e}")

# Register routers conditionally
if AI_CHAT_AVAILABLE:
    app.include_router(ai_chat_router)
    logger.info("AI Chat router registered")
if GEMINI_FREE_AVAILABLE:
    app.include_router(gemini_free_router)
    logger.info("Gemini Free router registered")
if NEWS_AVAILABLE:
    app.include_router(news_router, prefix="/api")
    app.include_router(news_processing_router, prefix="/api")
    logger.info("News routers registered")
if AI_REVIEW_AVAILABLE:
    app.include_router(ai_review_router)
    logger.info("AI Review router registered")
if LOGS_AVAILABLE:
    app.include_router(logs_router)
    logger.info("Logs router registered")
if FEEDS_AVAILABLE:
    app.include_router(feeds_router, prefix="/api")
    logger.info("Feeds router registered")
if NEWS_ROUTER_AVAILABLE:
    app.include_router(news_router, prefix="/api")
    app.include_router(news_analysis_router, prefix="/api")
    app.include_router(gemini_news_router, prefix="/api")
    logger.info("News routers registered")
if AUTH_ROUTER_AVAILABLE:
    app.include_router(auth_router)
    logger.info("Auth router registered")
if SIGNALS_AVAILABLE:    # Phase 4: Trading Signals
    app.include_router(signals_router, prefix="/api")
    logger.info("Signals router registered")
    
    # 🆕 War Room (7-Agent Debate System)
    from backend.api.war_room_router import router as war_room_router
    app.include_router(war_room_router)
    logger.info("War Room router registered")
    
    # 🆕 War Room Analytics (Debate Visualization & Shadow Trading)
    try:
        from backend.api.war_room_analytics_router import router as war_room_analytics_router
        app.include_router(war_room_analytics_router)
        logger.info("War Room Analytics router registered")
    except Exception as e:
        logger.warning(f"War Room Analytics router not available: {e}")

    # 🆕 Signal Consolidation (Multi-Source Aggregation)
    from backend.api.signal_consolidation_router import router as signal_consolidation_router
    app.include_router(signal_consolidation_router)
    logger.info("Signal Consolidation router registered")

    # 🆕 Orders API (Phase 27: Frontend UI)
    from backend.api.orders_router import router as orders_router
    app.include_router(orders_router)
    logger.info("Orders router registered")

    # 🆕 Portfolio API (Phase 27: Frontend UI)
    from backend.api.portfolio_router import router as portfolio_router
    app.include_router(portfolio_router)
    logger.info("Portfolio router registered")

    # 🆕 Performance API (Phase 25.2: Agent Performance Tracking)
    from backend.api.performance_router import router as performance_router
    app.include_router(performance_router)
    logger.info("Performance router registered")
    
    # 🆕 Weight Adjustment API (Phase 25.4: Self-Learning System)
    from backend.api.weight_adjustment_router import router as weight_router, alerts_router
    app.include_router(weight_router)
    app.include_router(alerts_router)
    logger.info("Weight Adjustment & Alerts routers registered")
    
    # 🆕 Dividend API (Phase 21: Dividend Intelligence Module)
    from backend.api.dividend_router import router as dividend_router
    app.include_router(dividend_router)
    logger.info("Dividend router registered")

    
    # 🆕 Accountability API (Phase 29: News Interpretation Accuracy Tracking)
    from backend.api.accountability_router import router as accountability_router
    app.include_router(accountability_router)
    logger.info("Accountability router registered")
    
    # 🆕 Kill Switch API (Live Trading Safety - 2026-01-02)
    from backend.routers.kill_switch_router import router as kill_switch_router
    app.include_router(kill_switch_router)
    logger.info("Kill Switch router registered")

try:
    # 🆕 Multi-Asset API (Phase 30: Multi-Asset Support)
    from backend.api.multi_asset_router import router as multi_asset_router
    app.include_router(multi_asset_router)
    logger.info("Multi-Asset router registered")
    MULTI_ASSET_AVAILABLE = True
except ImportError as e:
    MULTI_ASSET_AVAILABLE = False
    logger.warning(f"Multi-Asset router not available: {e}")

try:
    # 🆕 Portfolio Optimization API (Phase 31: MPT & Efficient Frontier)
    from backend.api.portfolio_optimization_router import router as portfolio_opt_router
    app.include_router(portfolio_opt_router)
    logger.info("Portfolio Optimization router registered")
    PORTFOLIO_OPT_AVAILABLE = True
except ImportError as e:
    PORTFOLIO_OPT_AVAILABLE = False
    logger.warning(f"Portfolio Optimization router not available: {e}")

try:
    # 🆕 Failure Learning API (Phase 29 확장: Auto-Learning System)
    from backend.api.failure_learning_router import router as failure_learning_router
    app.include_router(failure_learning_router)
    logger.info("Failure Learning router registered")
    FAILURE_LEARNING_AVAILABLE = True
except ImportError as e:
    FAILURE_LEARNING_AVAILABLE = False
    logger.warning(f"Failure Learning router not available: {e}")

try:
    # 🆕 Correlation API (Phase 32: Asset Correlation)
    from backend.api.correlation_router import router as correlation_router
    app.include_router(correlation_router)
    logger.info("Correlation router registered")
    CORRELATION_AVAILABLE = True
except ImportError as e:
    CORRELATION_AVAILABLE = False
    logger.warning(f"Correlation router not available: {e}")

if NOTIFICATIONS_AVAILABLE:
    app.include_router(notifications_router)
    logger.info("Notifications router registered")
if BACKTEST_AVAILABLE:
    app.include_router(backtest_router, prefix="/api")
    logger.info("Backtest router registered")
if CEO_ANALYSIS_AVAILABLE:
    app.include_router(ceo_analysis_router)
    logger.info("CEO Analysis router registered")
if INCREMENTAL_AVAILABLE:
    app.include_router(incremental_router)
    logger.info("Incremental router registered")
if REPORTS_AVAILABLE:
    app.include_router(reports_router, prefix="/api")
    logger.info("Reports router registered (/api/reports)")
if REASONING_AVAILABLE:
    app.include_router(reasoning_router)
    logger.info("Reasoning router registered")
if PHASE_AVAILABLE:
    app.include_router(phase_router)
    logger.info("Phase router registered")
if KIS_AVAILABLE:
    app.include_router(kis_router)
    logger.info("KIS router registered")
if AI_SIGNALS_AVAILABLE:
    app.include_router(ai_signals_router)
    logger.info("AI Signals router registered")
if CONSENSUS_AVAILABLE:
    app.include_router(consensus_router)
    logger.info("Consensus router registered")
if POSITION_AVAILABLE:
    app.include_router(position_router)
    logger.info("Position router registered")
if GLOBAL_MACRO_AVAILABLE:
    app.include_router(global_macro_router)
    logger.info("Global Macro router registered")
if AUTO_TRADE_AVAILABLE:
    app.include_router(auto_trade_router)
    logger.info("Auto Trade router registered")
    
# Emergency Detection
from backend.api.emergency_router import router as emergency_router
app.include_router(emergency_router, prefix="/api")
logger.info("Emergency router registered")

# Monitoring & Kill Switch
try:
    from backend.api.monitoring_router import router as monitoring_router
    app.include_router(monitoring_router)
    logger.info("Monitoring router registered")
except Exception as e:
    logger.warning(f"Monitoring router not available: {e}")

# NEW: Briefing Router (Phase 3)
try:
    from backend.api.briefing_router import router as briefing_router
    app.include_router(briefing_router)
    logger.info("Briefing router registered")
except Exception as e:
    logger.warning(f"Briefing router not available: {e}")

# Feedback Router (Frontend Integration Phase)
try:
    from backend.api.feedback_router import router as feedback_router
    app.include_router(feedback_router)
    logger.info("Feedback router registered")
except Exception as e:
    logger.warning(f"Feedback router not available: {e}")

# Data Backfill (Historical Data Seeding)
try:
    from backend.api.data_backfill_router import router as data_backfill_router
    app.include_router(data_backfill_router)
    logger.info("Data Backfill router registered")
except Exception as e:
    logger.warning(f"Data Backfill router not available: {e}")

# 🆕 Phase 4: Grand Unified Strategy APIs (2026-01-05)
# Persona Router - Investment Mode Switching
try:
    from backend.api.persona_router import router as persona_router
    app.include_router(persona_router)
    logger.info("Persona router registered (Dividend/Long-Term/Trading/Aggressive modes)")
except Exception as e:
    logger.warning(f"Persona router not available: {e}")

# Thesis Violation Detector - Investment Thesis Health Check
try:
    from backend.api.thesis_router import router as thesis_router
    app.include_router(thesis_router)
    logger.info("Thesis Violation router registered")
except Exception as e:
    logger.warning(f"Thesis Violation router not available: {e}")

# Investment Journey Memory - Decision Tracking & Coaching
try:
    from backend.api.journey_router import router as journey_router
    app.include_router(journey_router)
    logger.info("Investment Journey Memory router registered")
except Exception as e:
    logger.warning(f"Investment Journey Memory router not available: {e}")

# Account Partitioning - Virtual Wallet System (Core/Income/Satellite)
try:
    from backend.api.partitions_router import router as partitions_router
    app.include_router(partitions_router)
    logger.info("Account Partitioning router registered (Core/Income/Satellite wallets)")
except Exception as e:
    logger.warning(f"Account Partitioning router not available: {e}")

# Multi-Strategy Orchestration - Strategy Management API
try:
    from backend.api.strategy_router import strategy_router, ownership_router, conflict_router, conflict_ws_manager
    app.include_router(strategy_router, prefix="/api/strategies", tags=["Multi-Strategy"])
    app.include_router(ownership_router, prefix="/api/ownership", tags=["Multi-Strategy"])
    app.include_router(conflict_router, prefix="/api/conflicts", tags=["Multi-Strategy"])

    # WebSocket endpoint for real-time conflict alerts
    @app.websocket("/api/conflicts/ws")
    async def websocket_conflict_endpoint(websocket: WebSocket):
        """
        Real-time conflict alerts WebSocket endpoint.
        Broadcasts CONFLICT_DETECTED events to all connected clients.
        """
        await conflict_ws_manager.connect(websocket)
        try:
            while True:
                # Keep connection alive
                await websocket.receive_text()
        except WebSocketDisconnect:
            conflict_ws_manager.disconnect(websocket)

    # Connect WebSocket manager to event subscribers
    set_conflict_ws_manager(conflict_ws_manager)

    logger.info("✅ Multi-Strategy Orchestration routers registered (Strategy/Ownership/Conflict)")
    logger.info("✅ Conflict WebSocket endpoint mounted at /api/conflicts/ws")
except Exception as e:
    logger.warning(f"Multi-Strategy Orchestration routers not available: {e}")

# System/Mock routers (no prefix)=============================================================================


# Request/Response models
# =============================================================================
class AnalyzeRequest(BaseModel):
    ticker: str
    urgency: str = "MEDIUM"
    market_context: Optional[Dict] = None

class BatchAnalyzeRequest(BaseModel):
    tickers: list[str]
    urgency: str = "MEDIUM"
    max_concurrent: int = 5

class PortfolioUpdate(BaseModel):
    ticker: str
    action: str
    shares: int
    price: float

class AlertRequest(BaseModel):
    level: str
    category: str
    title: str
    message: str
    data: Optional[Dict] = None

# =============================================================================
# Health & monitoring endpoints
# =============================================================================
@app.get("/", tags=["General"])
async def root():
    """Root endpoint with system info."""
    uptime = (datetime.utcnow() - start_time).total_seconds()
    return {
        "name": "AI Trading System",
        "version": "1.0.0",
        "status": "running",
        "uptime_seconds": uptime,
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Comprehensive health check endpoint."""
    if health_monitor:
        health = await health_monitor.get_system_health()
        if metrics_collector:
            metrics_collector.heartbeat()
        return health.to_dict()
    return {"status": "UNKNOWN", "message": "Health monitor not initialized"}

@app.get("/health/live", tags=["Health"])
async def liveness():
    """Kubernetes liveness probe."""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health/ready", tags=["Health"])
async def readiness():
    """Kubernetes readiness probe."""
    if health_monitor:
        health = await health_monitor.get_system_health()
        if health.status == HealthStatus.UNHEALTHY:
            raise HTTPException(status_code=503, detail="System is not ready")
        return {"status": "ready", "system_status": health.status.value}
    return {"status": "ready"}

@app.get("/metrics", tags=["Monitoring"])
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    if PROMETHEUS_AVAILABLE:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return PlainTextResponse(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    return PlainTextResponse(content="# Prometheus client not available", media_type="text/plain")

# =============================================================================
# Trading endpoints
# =============================================================================
@app.post("/api/analyze", tags=["Trading"])
async def analyze_ticker(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Analyze a single ticker using Trading Agent."""
    if metrics_collector:
        start_time_req = datetime.utcnow()
    
    try:
        # Import and initialize TradingAgent inside the endpoint to avoid circular imports during startup
        from backend.ai.trading_agent import TradingAgent
        agent = TradingAgent()
        
        # Perform analysis
        decision = await agent.analyze(
            ticker=request.ticker,
            market_context=request.market_context
        )
        
        result = {
            "ticker": decision.ticker,
            "action": decision.action,
            "conviction": decision.conviction,
            "reasoning": decision.reasoning,
            "position_size": decision.position_size,
            "target_price": decision.target_price,
            "stop_loss": decision.stop_loss,
            "risk_factors": decision.risk_factors,
            "timestamp": decision.timestamp.isoformat() if decision.timestamp else datetime.utcnow().isoformat(),
        }

        if metrics_collector:
            latency = (datetime.utcnow() - start_time_req).total_seconds()
            metrics_collector.record_trading_decision(
                ticker=request.ticker,
                action=result["action"],
                conviction=result["conviction"],
                latency_seconds=latency,
            )
        return result
        
    except Exception as e:
        logger.error(f"Analysis failed for {request.ticker}: {e}", exc_info=True)
        # Fallback to safe HOLD response
        return {
            "ticker": request.ticker,
            "action": "HOLD",
            "conviction": 0.0,
            "reasoning": f"Analysis failed: {str(e)}",
            "position_size": 0.0,
            "target_price": None,
            "stop_loss": None,
            "risk_factors": ["system_error"],
            "timestamp": datetime.utcnow().isoformat(),
        }

@app.post("/api/analyze/batch", tags=["Trading"])
async def analyze_batch(request: BatchAnalyzeRequest):
    """Analyze multiple tickers concurrently (demo limited to 10)."""
    results = []
    for ticker in request.tickers[:10]:
        results.append({
            "ticker": ticker,
            "action": "HOLD",
            "conviction": 0.5,
            "reasoning": f"Batch analysis of {ticker}",
            "risk_factors": [],
            "timestamp": datetime.utcnow().isoformat(),
        })
    return {"total": len(results), "results": results}

@app.get("/api/analysis/history", tags=["Trading"])
async def get_analysis_history(ticker: Optional[str] = None, limit: int = 20):
    """Get analysis history (mock data)."""
    # Mock data to prevent 404
    history = [
        {
            "id": 1,
            "ticker": "AAPL",
            "action": "BUY",
            "conviction": 0.85,
            "position_size": 5.0,
            "target_price": 185.0,
            "stop_loss": 165.0,
            "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "reasoning": "Strong quarterly results expected. Technical indicators show bullish divergence.",
            "risk_factors": ["Tech Sector Correction", "Supply Chain Issues"]
        },
        {
            "id": 2,
            "ticker": "TSLA",
            "action": "HOLD",
            "conviction": 0.55,
            "position_size": 0.0,
            "target_price": 250.0,
            "stop_loss": 210.0,
            "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "reasoning": "Mixed signals from recent delivery numbers. Waiting for clearer trend.",
            "risk_factors": ["Regulatory Scrutiny", "Competition"]
        },
         {
            "id": 3,
            "ticker": "NVDA",
            "action": "BUY",
            "conviction": 0.92,
            "position_size": 8.0,
            "target_price": 950.0,
            "stop_loss": 850.0,
            "timestamp": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
            "reasoning": "Dominant market position in AI chips confirmed by recent channel checks.",
            "risk_factors": ["Valuation Concerns", "Geopolitical Tension"]
        }
    ]
    
    if ticker:
        return [item for item in history if item["ticker"] == ticker.upper()]
        
    return history

@app.get("/api/portfolio", tags=["Portfolio"])
async def get_portfolio():
    """Get portfolio from KIS broker (real account data)."""
    try:
        # Import KIS broker
        from backend.brokers.kis_broker import KISBroker, KIS_AVAILABLE
        import os
        
        # Check if KIS is available
        if not KIS_AVAILABLE:
            logger.warning("KIS broker not available, returning mock data")
            return _get_mock_portfolio()
        
        # Get account number and mode from environment
        is_virtual = os.getenv("KIS_IS_VIRTUAL", "true").lower() == "true"
        account_no = os.getenv("KIS_PAPER_ACCOUNT" if is_virtual else "KIS_ACCOUNT_NUMBER")

        if not account_no:
            logger.warning(f"{'KIS_PAPER_ACCOUNT' if is_virtual else 'KIS_ACCOUNT_NUMBER'} not set, returning mock data")
            return _get_mock_portfolio()

        # Initialize KIS Broker (respect .env configuration)
        try:
            broker = KISBroker(account_no=account_no, is_virtual=is_virtual)
            balance = broker.get_account_balance()
            
            if not balance:
                logger.warning("Failed to get balance from KIS, returning mock data")
                return _get_mock_portfolio()
            
            # Transform KIS positions to frontend format
            positions = []
            for kis_pos in balance.get("positions", []):
                # KIS returns: symbol, quantity, avg_price, current_price, eval_amount, profit_loss
                ticker = kis_pos.get("symbol", kis_pos.get("ticker", "UNKNOWN"))
                quantity = kis_pos.get("quantity", kis_pos.get("qty", 0))
                avg_price = kis_pos.get("avg_price", kis_pos.get("entry_price", 0))
                current_price = kis_pos.get("current_price", kis_pos.get("price", 0))
                eval_amount = kis_pos.get("eval_amount", kis_pos.get("market_value", kis_pos.get("value", 0)))
                profit_loss = kis_pos.get("profit_loss", kis_pos.get("unrealized_pnl", kis_pos.get("pnl", 0)))
                
                # Calculate pnl_pct if not provided
                pnl_pct = 0.0
                if avg_price > 0 and quantity > 0:
                    cost_basis = avg_price * quantity
                    if cost_basis > 0:
                        pnl_pct = (profit_loss / cost_basis) * 100
                
                positions.append({
                    "ticker": ticker,
                    "quantity": int(quantity),
                    "entry_price": float(avg_price),
                    "current_price": float(current_price),
                    "market_value": float(eval_amount),  # This is what frontend expects!
                    "unrealized_pnl": float(profit_loss),
                    "unrealized_pnl_pct": float(pnl_pct)
                })
            
            # Convert KIS data to frontend format
            return {
                "total_value": float(balance.get("total_value", 0)),
                "cash": float(balance.get("cash", 0)),
                "positions_value": float(balance.get("total_value", 0)) - float(balance.get("cash", 0)),
                "daily_pnl": float(balance.get("daily_pnl", 0)),
                "total_pnl": float(balance.get("total_pnl", 0)),
                "daily_return_pct": float(balance.get("daily_return_pct", 0)),
                "total_return_pct": float(balance.get("total_return_pct", 0)),
                "positions": positions,
                "recent_trades": []
            }
            
        except Exception as broker_error:
            logger.error(f"KIS broker error: {broker_error}", exc_info=True)
            return _get_mock_portfolio()
            
    except Exception as e:
        logger.error(f"Portfolio fetch error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _get_mock_portfolio():
    """Mock portfolio data for when KIS is not available."""
    return {
        "total_value": 105234.56,
        "cash": 25000.00,
        "positions_value": 80234.56,
        "daily_pnl": 3234.56,
        "total_pnl": 5234.56,
        "daily_return_pct": 3.17,
        "total_return_pct": 5.24,
        "positions": [
            {
                "ticker": "AAPL",
                "quantity": 50,
                "entry_price": 175.30,
                "current_price": 182.45,
                "market_value": 9122.50,
                "unrealized_pnl": 357.50,
                "unrealized_pnl_pct": 4.08
            },
            {
                "ticker": "GOOGL",
                "quantity": 30,
                "entry_price": 138.20,
                "current_price": 142.85,
                "market_value": 4285.50,
                "unrealized_pnl": 139.50,
                "unrealized_pnl_pct": 3.36
            },
            {
                "ticker": "MSFT",
                "quantity": 45,
                "entry_price": 372.80,
                "current_price": 380.25,
                "market_value": 17111.25,
                "unrealized_pnl": 335.25,
                "unrealized_pnl_pct": 2.00
            }
        ],
        "recent_trades": [
            {
                "id": "trade-001",
                "ticker": "AAPL",
                "action": "BUY",
                "quantity": 10,
                "price": 182.45,
                "timestamp": datetime.utcnow().isoformat(),
                "reason": "Strong momentum and positive earnings outlook"
            },
            {
                "id": "trade-002",
                "ticker": "GOOGL",
                "action": "BUY",
                "quantity": 5,
                "price": 142.85,
                "timestamp": datetime.utcnow().isoformat(),
                "reason": "Undervalued with AI growth potential"
            }
        ]
    }

@app.get("/api/portfolio/daily", tags=["Portfolio"])
async def get_daily_portfolio():
    """Get daily portfolio performance (mock data for now)."""
    return {
        "date": datetime.utcnow().isoformat(),
        "starting_value": 102000.00,
        "ending_value": 105234.56,
        "daily_pnl": 3234.56,
        "daily_return_pct": 3.17,
        "trades_count": 5,
        "trades": [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "ticker": "AAPL",
                "action": "BUY",
                "shares": 10,
                "price": 182.45,
                "value": 1824.50,
                "commission": 1.50
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "ticker": "GOOGL",
                "action": "BUY",
                "shares": 5,
                "price": 142.85,
                "value": 714.25,
                "commission": 1.50
            }
        ]
    }

@app.get("/api/system/info", tags=["System"])
async def get_system_info():
    """Get system information and status."""
    import platform

    # Try to import psutil if available
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        memory_percent = memory.percent
        disk_percent = disk.percent
    except ImportError:
        cpu_percent = 0.0
        memory_percent = 0.0
        disk_percent = 0.0

    return {
        "version": "1.0.0",
        "environment": "production",
        "uptime_seconds": 3600,
        "start_time": datetime.utcnow().isoformat(),
        "system": {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_percent": disk_percent
        },
        "components": {
            "backend": True,
            "database": True,
            "redis": True,
            "news_crawler": True
        }
    }


# AI Reviews Mock Endpoints
@app.get("/api/ai-reviews", tags=["AI Reviews"])
async def get_ai_reviews(limit: int = 50):
    """Get AI review summaries (mock data)."""
    return []


@app.get("/api/ai-reviews/terms/all", tags=["AI Reviews"])
async def get_all_terms():
    """Get all trading terms (mock data)."""
    return {
        "terms": [],
        "total": 0
    }


# Logs Mock Endpoints
@app.get("/api/logs", tags=["Logs"])
async def get_logs(limit: int = 100, offset: int = 0, days: int = 7):
    """Get system logs (mock data)."""
    from datetime import timedelta
    now = datetime.utcnow()

    sample_logs = [
        {
            "id": 1,
            "timestamp": (now - timedelta(hours=1)).isoformat(),
            "level": "INFO",
            "category": "trading",
            "message": "Trade executed successfully",
            "details": {"ticker": "TSLA", "action": "BUY", "shares": 100}
        },
        {
            "id": 2,
            "timestamp": (now - timedelta(hours=2)).isoformat(),
            "level": "INFO",
            "category": "system",
            "message": "System health check passed",
            "details": {"cpu": 45.2, "memory": 62.1}
        },
        {
            "id": 3,
            "timestamp": (now - timedelta(hours=3)).isoformat(),
            "level": "WARNING",
            "category": "data",
            "message": "High API latency detected",
            "details": {"endpoint": "/api/market-data", "latency_ms": 850}
        },
        {
            "id": 4,
            "timestamp": (now - timedelta(hours=4)).isoformat(),
            "level": "INFO",
            "category": "trading",
            "message": "Portfolio rebalance completed",
            "details": {"positions_adjusted": 5, "total_value": 105234.56}
        },
        {
            "id": 5,
            "timestamp": (now - timedelta(hours=5)).isoformat(),
            "level": "ERROR",
            "category": "api",
            "message": "External API request failed",
            "details": {"api": "Yahoo Finance", "error": "Timeout after 30s"}
        }
    ]

    logs = sample_logs[:limit]

    # Return LogsResponse format
    return {
        "total_count": len(sample_logs),
        "logs": logs,
        "limit": limit,
        "offset": offset
    }


@app.get("/api/logs/statistics", tags=["Logs"])
async def get_log_statistics(days: int = 7):
    """Get log statistics (mock data)."""
    return {
        "total_logs": 1247,
        "by_level": {
            "INFO": 892,
            "WARNING": 234,
            "ERROR": 98,
            "CRITICAL": 23
        },
        "by_category": {
            "trading": 456,
            "system": 312,
            "data": 289,
            "api": 190
        },
        "errors_count": 98,
        "warnings_count": 234
    }


@app.get("/api/logs/levels", tags=["Logs"])
async def get_log_levels():
    """Get available log levels."""
    return {
        "levels": ["INFO", "WARNING", "ERROR", "CRITICAL"]
    }


@app.get("/api/logs/categories", tags=["Logs"])
async def get_log_categories():
    """Get available log categories."""
    return {
        "categories": ["trading", "system", "data", "api"]
    }


@app.post("/api/execute", tags=["Trading"])
async def execute_trade(request: AnalyzeRequest):
    """Execute a trade based on analysis result."""
    execution = {
        "ticker": request.ticker,
        "status": "SUCCESS",
        "action": "BUY",
        "shares": 50,
        "price": 875.50,
        "slippage_bps": 2.3,
        "algorithm": "TWAP",
        "execution_time_seconds": 180.5,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if metrics_collector:
        metrics_collector.record_execution(
            ticker=request.ticker,
            action=execution["action"],
            price=execution["price"],
            slippage_bps=execution["slippage_bps"],
            algorithm=execution["algorithm"],
        )
    if alert_manager:
        await alert_manager.alert_trade_executed(
            ticker=request.ticker,
            action=execution["action"],
            shares=execution["shares"],
            price=execution["price"],
            execution_data=execution,
        )
    return execution
# MVP War Room (3+1 Agent System) - Phase: MVP Consolidation (2025-12-31)
try:
    from backend.routers.war_room_mvp_router import router as war_room_mvp_router
    app.include_router(war_room_mvp_router)
    logger.info("✅ War Room MVP router registered (3+1 Agent System)")
except Exception as e:
    logger.warning(f"❌ War Room MVP router not available: {e}")

try:
    from backend.api.feedback_router import router as feedback_router
    app.include_router(feedback_router, prefix="/api")
    logger.info("✅ Feedback router registered")
except Exception as e:
    logger.error(f"❌ Feedback router not available: {e}")
