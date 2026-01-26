"""
Minimal Test Server for Live Dashboard Testing
Phase 4 - Real-time Execution

Provides only the essential endpoints needed for Live Dashboard:
- /api/market-data/ws - Market Data WebSocket
- /api/conflicts/ws - Conflict WebSocket  
- /health - Health check
"""

import logging
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Trading System - Test Server",
    description="Minimal server for Live Dashboard testing",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For testing only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import WebSocket managers
try:
    from backend.api.market_data_ws import router as market_data_ws_router, market_data_ws_manager
    from backend.api.conflicts_ws import router as conflicts_ws_router
    
    # Include WebSocket routers
    app.include_router(market_data_ws_router, prefix="/api/market-data", tags=["WebSocket"])
    app.include_router(conflicts_ws_router, prefix="/api/conflicts", tags=["WebSocket"])
    logger.info("✅ WebSocket routers loaded successfully")
except ImportError as e:
    logger.error(f"❌ Failed to load WebSocket routers: {e}")
    logger.info("Creating minimal WebSocket endpoints...")
    
    # Create minimal WebSocket endpoints
    @app.websocket("/api/market-data/ws")
    async def market_data_websocket(websocket: WebSocket):
        await websocket.accept()
        logger.info("Market Data WebSocket connected")
        try:
            while True:
                data = await websocket.receive_text()
                logger.info(f"Received: {data}")
                await websocket.send_json({"type": "echo", "data": data})
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
    
    @app.websocket("/api/conflicts/ws")
    async def conflicts_websocket(websocket: WebSocket):
        await websocket.accept()
        logger.info("Conflicts WebSocket connected")
        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_json({"type": "conflict", "data": data})
        except Exception as e:
            logger.error(f"WebSocket error: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AI Trading System - Test Server",
        "version": "1.0.0",
        "websockets": {
            "market_data": "/api/market-data/ws",
            "conflicts": "/api/conflicts/ws"
        }
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "AI Trading System Test Server",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "market_data_ws": "ws://localhost:8001/api/market-data/ws",
            "conflicts_ws": "ws://localhost:8001/api/conflicts/ws"
        }
    }

if __name__ == "__main__":
    logger.info("="*60)
    logger.info("🚀 Starting AI Trading System Test Server")
    logger.info("="*60)
    logger.info("Server: http://localhost:8001")
    logger.info("Docs: http://localhost:8001/docs")
    logger.info("Market Data WS: ws://localhost:8001/api/market-data/ws")
    logger.info("Conflicts WS: ws://localhost:8001/api/conflicts/ws")
    logger.info("="*60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
