"""
Portfolio Optimization API Router

Phase 31: Portfolio Optimization
Date: 2025-12-30

Modern Portfolio Theory (MPT) API endpoints:
- POST /api/portfolio/optimize/sharpe - Maximize Sharpe Ratio
- POST /api/portfolio/optimize/min-variance - Minimum Variance Portfolio
- POST /api/portfolio/efficient-frontier - Efficient Frontier calculation
- POST /api/portfolio/monte-carlo - Monte Carlo simulation
- POST /api/portfolio/risk-parity - Risk Parity allocation

All endpoints require a list of asset symbols in the request body.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from decimal import Decimal
import sys
import os

# Add project root to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.services.portfolio_optimizer import PortfolioOptimizer

# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio Optimization"])

# ============================================================================
# Request/Response Models
# ============================================================================

class OptimizeRequest(BaseModel):
    """
    Request body for portfolio optimization endpoints

    Attributes:
        symbols: List of asset symbols (e.g., ["AAPL", "MSFT", "GOOGL", "TLT", "GLD"])
        period: Historical data period (e.g., "1y", "2y", "5y")
        risk_free_rate: Risk-free rate for Sharpe ratio (default: 0.02 = 2%)
    """
    symbols: List[str] = Field(..., min_items=2, max_items=20, description="Asset symbols (2-20 assets)")
    period: str = Field(default="1y", description="Historical period: 6mo, 1y, 2y, 5y, 10y")
    risk_free_rate: float = Field(default=0.02, ge=0.0, le=0.1, description="Risk-free rate (0.0-0.1)")


class MonteCarloRequest(OptimizeRequest):
    """
    Request body for Monte Carlo simulation

    Extends OptimizeRequest with simulation-specific parameters

    Attributes:
        num_simulations: Number of random portfolios to generate (default: 10,000)
    """
    num_simulations: int = Field(default=10000, ge=1000, le=50000, description="Number of simulations (1,000-50,000)")


class EfficientFrontierRequest(OptimizeRequest):
    """
    Request body for Efficient Frontier calculation

    Extends OptimizeRequest with frontier-specific parameters

    Attributes:
        num_points: Number of points on the frontier (default: 50)
    """
    num_points: int = Field(default=50, ge=10, le=200, description="Number of frontier points (10-200)")


# ============================================================================
# Helper Functions
# ============================================================================

def format_optimization_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format optimization result for JSON response

    Converts numpy arrays and Decimal types to JSON-serializable formats
    Renames fields to match frontend expectations

    Args:
        result: Raw optimization result from PortfolioOptimizer

    Returns:
        JSON-serializable dictionary with renamed fields:
        - annual_return → expected_return
        - annual_volatility → volatility
    """
    formatted = {}

    for key, value in result.items():
        # Convert weights dictionary
        if key == "weights" and isinstance(value, dict):
            formatted[key] = {
                symbol: float(weight) if isinstance(weight, (int, float, Decimal)) else weight
                for symbol, weight in value.items()
            }
        # Rename annual_return to expected_return (frontend compatibility)
        elif key == "annual_return":
            formatted["expected_return"] = float(value)
        # Rename annual_volatility to volatility (frontend compatibility)
        elif key == "annual_volatility":
            formatted["volatility"] = float(value)
        # Convert numeric values
        elif isinstance(value, (int, float, Decimal)):
            formatted[key] = float(value)
        # Keep other values as-is
        else:
            formatted[key] = value

    return formatted


# ============================================================================
# POST /api/portfolio/optimize/sharpe - Maximum Sharpe Ratio
# ============================================================================

@router.post("/optimize/sharpe")
async def optimize_sharpe_ratio(request: OptimizeRequest):
    """
    Optimize portfolio for maximum Sharpe Ratio

    **Modern Portfolio Theory (MPT)**:
    Sharpe Ratio = (Portfolio Return - Risk Free Rate) / Portfolio Volatility

    This optimization finds the portfolio weights that maximize risk-adjusted returns.

    **Request Body:**
    ```json
    {
        "symbols": ["AAPL", "MSFT", "GOOGL", "TLT", "GLD"],
        "period": "1y",
        "risk_free_rate": 0.02
    }
    ```

    **Response:**
    - weights: Dictionary of {symbol: weight} (sum = 1.0)
    - expected_return: Annual expected return (e.g., 0.25 = 25%)
    - volatility: Annual volatility (e.g., 0.15 = 15%)
    - sharpe_ratio: Risk-adjusted return metric

    **Example:**
    ```json
    {
        "weights": {"AAPL": 0.10, "GLD": 0.70, "GOOGL": 0.20},
        "expected_return": 0.403,
        "volatility": 0.157,
        "sharpe_ratio": 2.31
    }
    ```
    """
    try:
        # Initialize optimizer with risk-free rate
        optimizer = PortfolioOptimizer(risk_free_rate=request.risk_free_rate)

        # Fetch historical price data
        data = optimizer.fetch_price_data(request.symbols, period=request.period)

        if data.empty:
            raise HTTPException(
                status_code=400,
                detail=f"No price data available for symbols: {request.symbols}"
            )

        # Calculate daily returns
        returns = optimizer.calculate_returns(data)

        # Optimize for maximum Sharpe ratio
        result = optimizer.optimize_sharpe_ratio(returns)

        # Format and return result
        return {
            "optimization_type": "Maximum Sharpe Ratio",
            "symbols": request.symbols,
            "period": request.period,
            "risk_free_rate": request.risk_free_rate,
            **format_optimization_result(result)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {str(e)}"
        )


# ============================================================================
# POST /api/portfolio/optimize/min-variance - Minimum Variance
# ============================================================================

@router.post("/optimize/min-variance")
async def optimize_min_variance(request: OptimizeRequest):
    """
    Optimize portfolio for minimum variance (lowest risk)

    **Modern Portfolio Theory (MPT)**:
    This optimization finds the portfolio with the lowest possible volatility
    while maintaining full investment (weights sum to 1).

    **Use Case**: Conservative investors prioritizing capital preservation

    **Request Body:**
    ```json
    {
        "symbols": ["AAPL", "MSFT", "TLT", "GLD"],
        "period": "2y"
    }
    ```

    **Response:**
    - weights: Dictionary of {symbol: weight} (sum = 1.0)
    - expected_return: Annual expected return
    - volatility: Annual volatility (minimized)
    - sharpe_ratio: Risk-adjusted return

    **Note**: Min variance portfolios typically have lower returns but also lower risk
    """
    try:
        # Initialize optimizer
        optimizer = PortfolioOptimizer(risk_free_rate=request.risk_free_rate)

        # Fetch historical price data
        data = optimizer.fetch_price_data(request.symbols, period=request.period)

        if data.empty:
            raise HTTPException(
                status_code=400,
                detail=f"No price data available for symbols: {request.symbols}"
            )

        # Calculate daily returns
        returns = optimizer.calculate_returns(data)

        # Optimize for minimum variance
        result = optimizer.optimize_min_variance(returns)

        # Format and return result
        return {
            "optimization_type": "Minimum Variance",
            "symbols": request.symbols,
            "period": request.period,
            "risk_free_rate": request.risk_free_rate,
            **format_optimization_result(result)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {str(e)}"
        )


# ============================================================================
# POST /api/portfolio/efficient-frontier - Efficient Frontier
# ============================================================================

@router.post("/efficient-frontier")
async def calculate_efficient_frontier(request: EfficientFrontierRequest):
    """
    Calculate the Efficient Frontier

    **Modern Portfolio Theory (MPT)**:
    The efficient frontier shows the set of optimal portfolios that offer
    the highest expected return for each level of risk.

    **Request Body:**
    ```json
    {
        "symbols": ["AAPL", "MSFT", "GOOGL", "TLT", "GLD"],
        "period": "1y",
        "num_points": 50
    }
    ```

    **Response:**
    - frontier: Array of {return, volatility, sharpe_ratio} points
    - min_volatility: Minimum variance portfolio point
    - max_sharpe: Maximum Sharpe ratio portfolio point

    **Visualization**: Plot return (Y) vs volatility (X) to see the curve

    **Example:**
    ```json
    {
        "frontier": [
            {"return": 0.25, "volatility": 0.14, "sharpe_ratio": 1.5},
            {"return": 0.30, "volatility": 0.15, "sharpe_ratio": 1.8},
            ...
        ],
        "count": 50
    }
    ```
    """
    try:
        # Initialize optimizer
        optimizer = PortfolioOptimizer(risk_free_rate=request.risk_free_rate)

        # Fetch historical price data
        data = optimizer.fetch_price_data(request.symbols, period=request.period)

        if data.empty:
            raise HTTPException(
                status_code=400,
                detail=f"No price data available for symbols: {request.symbols}"
            )

        # Calculate daily returns
        returns = optimizer.calculate_returns(data)

        # Calculate efficient frontier
        frontier_points = optimizer.efficient_frontier(returns, num_points=request.num_points)

        # Convert to JSON-serializable format
        frontier = [
            {
                "return": float(point["return"]),
                "volatility": float(point["volatility"]),
                "sharpe_ratio": float(point["sharpe_ratio"])
            }
            for point in frontier_points
        ]

        # Find min volatility and max Sharpe points
        min_vol_point = min(frontier, key=lambda x: x["volatility"])
        max_sharpe_point = max(frontier, key=lambda x: x["sharpe_ratio"])

        return {
            "optimization_type": "Efficient Frontier",
            "symbols": request.symbols,
            "period": request.period,
            "risk_free_rate": request.risk_free_rate,
            "frontier": frontier,
            "count": len(frontier),
            "min_volatility_point": min_vol_point,
            "max_sharpe_point": max_sharpe_point
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Efficient frontier calculation failed: {str(e)}"
        )


# ============================================================================
# POST /api/portfolio/monte-carlo - Monte Carlo Simulation
# ============================================================================

@router.post("/monte-carlo")
async def monte_carlo_simulation(request: MonteCarloRequest):
    """
    Run Monte Carlo simulation for portfolio optimization

    **Monte Carlo Method**:
    Generate thousands of random portfolio allocations and evaluate each one.
    This provides a statistical view of the risk-return tradeoff.

    **Request Body:**
    ```json
    {
        "symbols": ["AAPL", "MSFT", "GOOGL", "TLT", "GLD"],
        "period": "1y",
        "num_simulations": 10000
    }
    ```

    **Response:**
    - simulations: Array of {return, volatility, sharpe_ratio, weights} for each portfolio
    - best_sharpe: Portfolio with highest Sharpe ratio
    - min_volatility: Portfolio with lowest volatility
    - statistics: Min/Max/Avg for return, volatility, sharpe_ratio

    **Use Case**:
    - Visualize the risk-return landscape
    - Identify outlier portfolios
    - Validate efficient frontier results

    **Warning**: Large num_simulations (>20,000) may take longer to compute
    """
    try:
        # Initialize optimizer
        optimizer = PortfolioOptimizer(risk_free_rate=request.risk_free_rate)

        # Fetch historical price data
        data = optimizer.fetch_price_data(request.symbols, period=request.period)

        if data.empty:
            raise HTTPException(
                status_code=400,
                detail=f"No price data available for symbols: {request.symbols}"
            )

        # Calculate daily returns
        returns = optimizer.calculate_returns(data)

        # Run Monte Carlo simulation
        simulations = optimizer.monte_carlo_simulation(
            returns,
            num_simulations=request.num_simulations
        )

        # Convert to JSON-serializable format
        formatted_sims = []
        for sim in simulations:
            formatted_sims.append({
                "return": float(sim["return"]),
                "volatility": float(sim["volatility"]),
                "sharpe_ratio": float(sim["sharpe_ratio"]),
                "weights": {
                    symbol: float(weight)
                    for symbol, weight in sim["weights"].items()
                }
            })

        # Find best portfolios
        best_sharpe = max(formatted_sims, key=lambda x: x["sharpe_ratio"])
        min_vol = min(formatted_sims, key=lambda x: x["volatility"])

        # Calculate statistics
        returns_list = [s["return"] for s in formatted_sims]
        vols_list = [s["volatility"] for s in formatted_sims]
        sharpes_list = [s["sharpe_ratio"] for s in formatted_sims]

        statistics = {
            "return": {
                "min": min(returns_list),
                "max": max(returns_list),
                "avg": sum(returns_list) / len(returns_list)
            },
            "volatility": {
                "min": min(vols_list),
                "max": max(vols_list),
                "avg": sum(vols_list) / len(vols_list)
            },
            "sharpe_ratio": {
                "min": min(sharpes_list),
                "max": max(sharpes_list),
                "avg": sum(sharpes_list) / len(sharpes_list)
            }
        }

        return {
            "optimization_type": "Monte Carlo Simulation",
            "symbols": request.symbols,
            "period": request.period,
            "risk_free_rate": request.risk_free_rate,
            "num_simulations": request.num_simulations,
            "simulations": formatted_sims,
            "best_sharpe_portfolio": best_sharpe,
            "min_volatility_portfolio": min_vol,
            "statistics": statistics
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Monte Carlo simulation failed: {str(e)}"
        )


# ============================================================================
# POST /api/portfolio/risk-parity - Risk Parity Allocation
# ============================================================================

@router.post("/risk-parity")
async def risk_parity_allocation(request: OptimizeRequest):
    """
    Calculate Risk Parity portfolio allocation

    **Risk Parity Strategy**:
    Allocate capital such that each asset contributes equally to portfolio risk.
    This ensures diversification across risk sources, not just dollar amounts.

    **Concept**:
    - Traditional 60/40 stock/bond: stocks dominate risk
    - Risk Parity: bonds get higher allocation to balance risk contribution

    **Request Body:**
    ```json
    {
        "symbols": ["SPY", "TLT", "GLD", "VNQ"],
        "period": "2y"
    }
    ```

    **Response:**
    - weights: Dictionary of {symbol: weight} (sum = 1.0)
    - risk_contributions: Each asset's contribution to total portfolio risk
    - expected_return: Annual expected return
    - volatility: Annual volatility
    - sharpe_ratio: Risk-adjusted return

    **Use Case**:
    - Popular in institutional investing (Bridgewater's All Weather Fund)
    - Reduces concentration risk
    - More stable during market volatility
    """
    try:
        # Initialize optimizer
        optimizer = PortfolioOptimizer(risk_free_rate=request.risk_free_rate)

        # Fetch historical price data
        data = optimizer.fetch_price_data(request.symbols, period=request.period)

        if data.empty:
            raise HTTPException(
                status_code=400,
                detail=f"No price data available for symbols: {request.symbols}"
            )

        # Calculate daily returns
        returns = optimizer.calculate_returns(data)

        # Calculate Risk Parity allocation
        result = optimizer.risk_parity_allocation(returns)

        # Format and return result
        return {
            "optimization_type": "Risk Parity",
            "symbols": request.symbols,
            "period": request.period,
            "risk_free_rate": request.risk_free_rate,
            **format_optimization_result(result)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Risk parity calculation failed: {str(e)}"
        )
