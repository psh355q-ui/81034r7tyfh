"""
Example usage of ELK Logger
Demonstrates how to integrate structured logging in your application
"""

from backend.utils.elk_logger import get_elk_logger, log_api_call
from fastapi import FastAPI, Request
import time

# Initialize ELK Logger
elk_logger = get_elk_logger(
    service_name="ai-trading-backend",
    logstash_host="localhost",
    logstash_port=5000
)

app = FastAPI()


# Example 1: Basic logging
@app.get("/")
async def root():
    elk_logger.info("Homepage accessed")
    return {"message": "Welcome to AI Trading System"}


# Example 2: API request logging with decorator
@app.get("/stock/{ticker}")
@log_api_call(elk_logger)
async def get_stock(ticker: str, request: Request):
    elk_logger.info(
        f"Fetching stock data for {ticker}",
        ticker=ticker,
        endpoint="/stock"
    )

    # Simulate data fetching
    stock_data = {"ticker": ticker, "price": 150.25}

    return stock_data


# Example 3: Trading activity logging
@app.post("/trade")
async def execute_trade(ticker: str, action: str, quantity: int):
    try:
        price = 150.25  # Fetch from market

        elk_logger.log_trading_activity(
            action=action,
            ticker=ticker,
            quantity=quantity,
            price=price,
            order_id="ORD-12345",
            strategy="momentum"
        )

        return {"status": "success", "order_id": "ORD-12345"}

    except Exception as e:
        elk_logger.log_exception(
            e,
            context={"ticker": ticker, "action": action}
        )
        raise


# Example 4: AI request logging (cost tracking)
@app.get("/ai/analyze/{ticker}")
async def ai_analyze(ticker: str):
    start_time = time.time()

    try:
        # Simulate OpenAI call
        prompt_tokens = 1500
        completion_tokens = 500
        cost = (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000

        duration_ms = (time.time() - start_time) * 1000

        elk_logger.log_ai_request(
            model="gpt-4",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost,
            duration_ms=duration_ms,
            ticker=ticker,
            task="stock_analysis"
        )

        return {"analysis": "Bullish trend detected"}

    except Exception as e:
        elk_logger.log_exception(e, context={"ticker": ticker})
        raise


# Example 5: Database query logging
async def fetch_from_db(ticker: str):
    start_time = time.time()

    # Simulate DB query
    query = f"SELECT * FROM stocks WHERE ticker = '{ticker}'"

    # Simulate query execution
    time.sleep(0.012)  # 12ms query

    duration_ms = (time.time() - start_time) * 1000

    elk_logger.log_database_query(
        query=query,
        duration_ms=duration_ms,
        rows_affected=1,
        ticker=ticker
    )

    return {"data": "stock_data"}


# Example 6: Cache operation logging
async def get_from_cache(key: str):
    start_time = time.time()

    # Simulate cache lookup
    cache_hit = True

    duration_ms = (time.time() - start_time) * 1000

    elk_logger.log_cache_operation(
        operation="GET",
        key=key,
        hit=cache_hit,
        duration_ms=duration_ms
    )

    return "cached_value" if cache_hit else None


# Example 7: Error logging
@app.get("/error-example")
async def error_example():
    try:
        result = 1 / 0  # Intentional error
    except Exception as e:
        elk_logger.error(
            "Division by zero error",
            endpoint="/error-example",
            user_id="user-123"
        )
        elk_logger.log_exception(e, context={"endpoint": "/error-example"})
        raise


# Example 8: Warning logging
@app.get("/slow-api")
async def slow_api():
    start_time = time.time()
    time.sleep(2)  # Simulate slow operation
    duration_ms = (time.time() - start_time) * 1000

    if duration_ms > 1000:
        elk_logger.warning(
            f"Slow API response: {duration_ms:.2f}ms",
            endpoint="/slow-api",
            duration_ms=duration_ms,
            threshold_ms=1000
        )

    return {"status": "completed"}


# Example 9: Custom structured logging
@app.get("/custom-log")
async def custom_log():
    elk_logger.info(
        "Custom business event",
        event_type="user_signup",
        user_id="user-456",
        plan="premium",
        referral_code="FRIEND123",
        metadata={
            "source": "mobile_app",
            "campaign": "summer_2024"
        }
    )

    return {"status": "logged"}


# Example 10: Batch operation logging
@app.post("/batch-process")
async def batch_process():
    tickers = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]

    elk_logger.info(
        f"Starting batch processing for {len(tickers)} tickers",
        operation="batch_process",
        ticker_count=len(tickers),
        tickers=tickers
    )

    processed = 0
    errors = 0

    for ticker in tickers:
        try:
            # Process ticker
            time.sleep(0.1)
            processed += 1
        except Exception as e:
            errors += 1
            elk_logger.log_exception(e, context={"ticker": ticker})

    elk_logger.info(
        f"Batch processing completed: {processed} success, {errors} errors",
        operation="batch_process",
        processed=processed,
        errors=errors,
        total=len(tickers)
    )

    return {
        "processed": processed,
        "errors": errors,
        "total": len(tickers)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
