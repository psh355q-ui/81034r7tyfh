"""
Run Trading Dashboard API Server

Starts FastAPI server for trading signals and portfolio management.

Usage:
    python scripts/run_api_server.py

    # Custom port
    python scripts/run_api_server.py --port 8080

    # Production mode
    python scripts/run_api_server.py --production
"""

import sys
from pathlib import Path
import argparse

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
from backend.api.main import app


def main():
    parser = argparse.ArgumentParser(description="Run AI Trading System API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--production", action="store_true", help="Run in production mode (no reload)")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes (production only)")

    args = parser.parse_args()

    print("=" * 80)
    print("AI Trading System API Server")
    print("=" * 80)
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Mode: {'Production' if args.production else 'Development'}")
    print("=" * 80)
    print(f"\n📡 API Documentation: http://localhost:{args.port}/docs")
    print(f"🔌 WebSocket Endpoint: ws://localhost:{args.port}/ws/signals")
    print("\n" + "=" * 80)

    if args.production:
        # Production: Multiple workers, no reload
        uvicorn.run(
            "backend.api.main:app",
            host=args.host,
            port=args.port,
            workers=args.workers,
            log_level="info"
        )
    else:
        # Development: Auto-reload
        uvicorn.run(
            "backend.api.main:app",
            host=args.host,
            port=args.port,
            reload=True,
            log_level="debug"
        )


if __name__ == "__main__":
    main()
