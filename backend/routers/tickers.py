"""
Ticker Autocomplete API Router
Provides dynamic ticker lists for frontend autocomplete functionality
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import json
import os
from pathlib import Path

router = APIRouter(prefix="/api/tickers", tags=["tickers"])

# Path to tickers JSON file
TICKERS_FILE = Path(__file__).parent.parent / "data" / "tickers.json"


@router.get("/autocomplete")
async def get_autocomplete_tickers():
    """
    Get ticker autocomplete data with version control
    
    Returns:
        - version: Data version (YYYY.MM.DD format)
        - last_updated: ISO timestamp
        - tickers: Dictionary containing ticker arrays and Korean name mappings
    """
    try:
        # Load ticker data from JSON file
        with open(TICKERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Add server timestamp
        data["server_time"] = datetime.utcnow().isoformat() + "Z"
        
        return data
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail=f"Ticker data file not found: {TICKERS_FILE}"
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON in ticker data file: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading ticker data: {str(e)}"
        )


@router.get("/version")
async def get_ticker_version():
    """
    Get current ticker data version (lightweight check)
    
    Returns:
        - version: Current data version
        - last_updated: Last update timestamp
    """
    try:
        with open(TICKERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return {
            "version": data.get("version"),
            "last_updated": data.get("last_updated"),
            "server_time": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading version: {str(e)}"
        )
