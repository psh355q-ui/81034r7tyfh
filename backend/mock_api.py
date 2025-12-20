"""
Mock API Server for Frontend Development
Simple FastAPI server with mock data
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import random

app = FastAPI(title="AI Trading System - Mock API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/portfolio")
async def get_portfolio():
    return {
        "total_value": 105234.56,
        "cash": 25000.00,
        "invested_value": 80234.56,
        "total_pnl": 5234.56,
        "total_return_pct": 5.24,
        "positions": [
            {
                "ticker": "AAPL",
                "shares": 50,
                "avg_price": 175.30,
                "current_price": 182.45,
                "value": 9122.50,
                "unrealized_pnl": 357.50,
                "pnl_pct": 4.08
            },
            {
                "ticker": "GOOGL",
                "shares": 30,
                "avg_price": 138.20,
                "current_price": 142.85,
                "value": 4285.50,
                "unrealized_pnl": 139.50,
                "pnl_pct": 3.36
            },
            {
                "ticker": "MSFT",
                "shares": 45,
                "avg_price": 372.80,
                "current_price": 380.25,
                "value": 17111.25,
                "unrealized_pnl": 335.25,
                "pnl_pct": 2.00
            }
        ]
    }

@app.get("/portfolio/daily")
async def get_daily_portfolio():
    return {
        "date": datetime.now().isoformat(),
        "starting_value": 102000.00,
        "ending_value": 105234.56,
        "daily_pnl": 3234.56,
        "daily_return_pct": 3.17,
        "trades_count": 5,
        "trades": [
            {
                "timestamp": datetime.now().isoformat(),
                "ticker": "AAPL",
                "action": "BUY",
                "shares": 10,
                "price": 182.45,
                "value": 1824.50,
                "commission": 1.50
            },
            {
                "timestamp": datetime.now().isoformat(),
                "ticker": "GOOGL",
                "action": "BUY",
                "shares": 5,
                "price": 142.85,
                "value": 714.25,
                "commission": 1.50
            }
        ]
    }

@app.post("/analyze")
async def analyze_ticker(request: dict):
    ticker = request.get("ticker", "UNKNOWN")
    return {
        "ticker": ticker,
        "action": random.choice(["BUY", "SELL", "HOLD"]),
        "conviction": round(random.uniform(0.6, 0.95), 2),
        "reasoning": f"Based on technical analysis, {ticker} shows strong momentum.",
        "target_price": round(random.uniform(150, 200), 2),
        "stop_loss": round(random.uniform(140, 150), 2),
        "position_size": round(random.uniform(3, 10), 1),
        "risk_factors": ["market_volatility", "earnings_risk"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/risk/status")
async def get_risk_status():
    return {
        "kill_switch_active": False,
        "daily_pnl": 3234.56,
        "daily_return_pct": 3.17,
        "max_drawdown_pct": -2.5,
        "position_concentration": {
            "MSFT": 35.2,
            "AAPL": 18.7,
            "GOOGL": 8.8
        },
        "sector_concentration": {
            "Technology": 62.7,
            "Finance": 22.3,
            "Healthcare": 15.0
        },
        "risk_alerts": []
    }

@app.post("/risk/kill-switch/activate")
async def activate_kill_switch():
    return {"status": "success", "message": "Kill switch activated"}

@app.post("/risk/kill-switch/deactivate")
async def deactivate_kill_switch():
    return {"status": "success", "message": "Kill switch deactivated"}

@app.get("/alerts")
async def get_alerts(limit: int = 10):
    return []

@app.get("/system/info")
async def get_system_info():
    return {
        "version": "1.0.0",
        "environment": "development",
        "uptime_seconds": 3600,
        "start_time": datetime.now().isoformat(),
        "components": {
            "redis": True,
            "timescaledb": True,
            "claude_api": True
        },
        "config": {
            "mode": "paper_trading",
            "initial_capital": 100000.0
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
