
from fastapi import APIRouter
from typing import List, Dict

router = APIRouter()

@router.get("/logs", response_model=List[Dict])
async def get_shadow_logs():
    """
    Get recent shadow trading logs.
    """
    # Mock Data for MVP Frontend Dev
    return [
        {
            "timestamp": "2024-05-20T10:00:00",
            "ticker": "AAPL",
            "intent": {"direction": "BUY", "score": 0.8, "rationale": ["News Positive"]},
            "status": "SHADOW_FILLED",
            "execution": {"action": 2, "price": 150.0}
        },
        {
            "timestamp": "2024-05-20T10:05:00",
            "ticker": "NVDA",
            "intent": {"direction": "HOLD", "score": 0.1, "rationale": ["Low Volume"]},
            "status": "SKIPPED",
            "execution": None
        }
    ]

@router.get("/graph", response_model=Dict)
async def get_gnn_graph():
    """
    Get current GNN graph structure.
    """
    # Mock Graph: Cluster around NVDA
    return {
        "nodes": [
            {"id": "NVDA", "group": "Chip"},
            {"id": "AMD", "group": "Chip"},
            {"id": "TSLA", "group": "Auto"}
        ],
        "links": [
            {"source": "NVDA", "target": "AMD", "value": 1.0},
            {"source": "NVDA", "target": "TSLA", "value": 0.5}
        ]
    }
