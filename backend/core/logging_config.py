"""
logging_config.py - JSON 구조화 로깅 (ELK Stack)

📊 Data Sources:
    - Application Events: API requests, Trading actions, AI requests
    - Log Output: JSON formatted logs → Logstash → Elasticsearch
    - File & Console: Dual output (file for persistence, console for dev)

🔗 External Dependencies:
    - logging (stdlib): Python logging framework
    - json (stdlib): JSON serialization
    - sys, traceback: Error stack traces

📤 Classes & Functions:
    - JSONFormatter: Custom JSON log formatter
        - service_name, environment, timestamp, level, message
        - Extra fields: ticker, action, duration, cost_usd
    - StructuredLogger: Wrapper for structured logging
        - api_request(): API 요청 로깅 (endpoint, method, status, duration)
        - trading_action(): 거래 로깅 (ticker, quantity, price, order_id)
        - ai_request(): AI API 로깅 (model, tokens, cost, duration)
        - database_query(): DB 쿼리 로깅 (query_type, duration, rows_affected)
        - error(), warning(), info(), debug(): Standard log levels
    - setup_logging(): Initialize structured logging
    - get_logger(name): Get StructuredLogger instance

🔄 Used By (전체 시스템):
    - backend/api/*.py: API request logging
    - backend/ai/*.py: AI request cost tracking
    - backend/services/*.py: Background job logging
    - backend/data/*.py: Data collection logging

📝 Notes:
    - ELK Stack Integration: JSON → Logstash → Elasticsearch → Kibana
    - Custom Fields: ticker, action, cost_usd for domain-specific logging
    - Structured Data: All logs parsable by Elasticsearch
    - Performance Tracking: duration, tokens, rows_affected
    - Error Context: exc_info, stack_trace included

This module provides JSON-formatted logging for easy parsing by Logstash/Elasticsearch.
"""

import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    Outputs logs in JSON format compatible with ELK Stack.
    """

    def __init__(
        self,
        service_name: str = "ai-trading-backend",
        environment: str = "production",
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.service_name = service_name
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""

        # Base log structure
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "environment": self.environment,
        }

        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": "".join(traceback.format_exception(*record.exc_info)),
            }

        # Add extra fields from record
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        # Common extracted fields for trading system
        extra_fields = [
            "ticker",
            "user_id",
            "order_id",
            "endpoint",
            "path",
            "duration",
            "response_time",
            "status_code",
            "client_ip",
            "user_agent",
            "cost_usd",
            "model",
            "tokens",
            "confidence",
            "action",
            "quantity",
            "price",
        ]

        for field in extra_fields:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)

        # Add function and line info for debugging
        log_data["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }

        return json.dumps(log_data, default=str, ensure_ascii=False)


def setup_logging(
    service_name: str = "ai-trading-backend",
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    environment: str = "production",
) -> None:
    """
    Setup structured JSON logging for the application.

    Args:
        service_name: Name of the service for log identification
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for file logging
        environment: Environment name (production, development, testing)
    """

    # Create JSON formatter
    json_formatter = JSONFormatter(
        service_name=service_name,
        environment=environment,
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler (stdout) - JSON format for Docker logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(json_formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional) - for persistent logs
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(json_formatter)
        root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Log initialization
    root_logger.info(
        "Logging initialized",
        extra={
            "service": service_name,
            "environment": environment,
            "log_level": log_level,
            "log_file": log_file,
        },
    )


class StructuredLogger:
    """
    Wrapper class for structured logging with common fields.
    Provides convenient methods for different log types.
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration: float,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        **kwargs
    ):
        """Log API request with structured data."""
        self.logger.info(
            f"{method} {endpoint} - {status_code}",
            extra={
                "type": "api_request",
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "duration": duration,
                "client_ip": client_ip,
                "user_agent": user_agent,
                **kwargs,
            },
        )

    def trading_action(
        self,
        action: str,
        ticker: str,
        quantity: Optional[float] = None,
        price: Optional[float] = None,
        order_id: Optional[str] = None,
        **kwargs
    ):
        """Log trading action."""
        self.logger.info(
            f"Trading: {action} {ticker}",
            extra={
                "type": "trading_action",
                "action": action,
                "ticker": ticker,
                "quantity": quantity,
                "price": price,
                "order_id": order_id,
                **kwargs,
            },
        )

    def ai_request(
        self,
        model: str,
        tokens: Optional[int] = None,
        cost_usd: Optional[float] = None,
        duration: Optional[float] = None,
        **kwargs
    ):
        """Log AI API request with cost tracking."""
        self.logger.info(
            f"AI Request: {model}",
            extra={
                "type": "ai_request",
                "model": model,
                "tokens": tokens,
                "cost_usd": cost_usd,
                "duration": duration,
                **kwargs,
            },
        )

    def database_query(
        self,
        query_type: str,
        duration: float,
        rows_affected: Optional[int] = None,
        **kwargs
    ):
        """Log database query performance."""
        self.logger.info(
            f"DB Query: {query_type}",
            extra={
                "type": "database_query",
                "query_type": query_type,
                "query_duration_ms": duration * 1000,  # Convert to ms
                "rows_affected": rows_affected,
                **kwargs,
            },
        )

    def error(self, message: str, exc_info=None, **kwargs):
        """Log error with optional exception."""
        self.logger.error(
            message,
            exc_info=exc_info,
            extra={
                "type": "error",
                **kwargs,
            },
        )

    def warning(self, message: str, **kwargs):
        """Log warning."""
        self.logger.warning(
            message,
            extra={
                "type": "warning",
                **kwargs,
            },
        )

    def info(self, message: str, **kwargs):
        """Log info."""
        self.logger.info(
            message,
            extra={
                "type": "info",
                **kwargs,
            },
        )

    def debug(self, message: str, **kwargs):
        """Log debug."""
        self.logger.debug(
            message,
            extra={
                "type": "debug",
                **kwargs,
            },
        )


# Convenience function to get structured logger
def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)
