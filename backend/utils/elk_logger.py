"""
ELK Stack Integration - Structured Logging
Sends structured JSON logs to Logstash for centralized logging
"""

import logging
import json
import socket
import time
from datetime import datetime
from typing import Any, Dict, Optional
from functools import wraps
import traceback


class ELKLogger:
    """Structured logger for ELK Stack integration"""

    def __init__(
        self,
        service_name: str,
        logstash_host: str = "localhost",
        logstash_port: int = 5000,
        environment: str = "production"
    ):
        self.service_name = service_name
        self.logstash_host = logstash_host
        self.logstash_port = logstash_port
        self.environment = environment
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(logging.INFO)

        # Try to connect to Logstash
        self.socket = None
        self._connect()

    def _connect(self):
        """Connect to Logstash TCP input"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.logstash_host, self.logstash_port))
        except Exception as e:
            print(f"Failed to connect to Logstash: {e}")
            self.socket = None

    def _send_log(self, log_data: Dict[str, Any]):
        """Send log to Logstash"""
        if not self.socket:
            # Fallback to console logging
            print(json.dumps(log_data))
            return

        try:
            message = json.dumps(log_data) + "\n"
            self.socket.sendall(message.encode('utf-8'))
        except Exception as e:
            print(f"Failed to send log to Logstash: {e}")
            # Try to reconnect
            self._connect()

    def _create_log_entry(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create structured log entry"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "service": self.service_name,
            "environment": self.environment,
            "message": message,
        }

        if extra:
            log_entry.update(extra)

        return log_entry

    def info(self, message: str, **kwargs):
        """Log info message"""
        log_entry = self._create_log_entry("INFO", message, kwargs)
        self._send_log(log_entry)
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        log_entry = self._create_log_entry("WARNING", message, kwargs)
        self._send_log(log_entry)
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        log_entry = self._create_log_entry("ERROR", message, kwargs)
        self._send_log(log_entry)
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        log_entry = self._create_log_entry("CRITICAL", message, kwargs)
        self._send_log(log_entry)
        self.logger.critical(message, extra=kwargs)

    def log_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        **kwargs
    ):
        """Log API request with structured data"""
        log_entry = self._create_log_entry(
            "INFO",
            f"{method} {endpoint} - {status_code}",
            {
                "type": "api_request",
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "user_id": user_id,
                **kwargs
            }
        )
        self._send_log(log_entry)

    def log_trading_activity(
        self,
        action: str,
        ticker: str,
        quantity: int,
        price: float,
        order_id: Optional[str] = None,
        **kwargs
    ):
        """Log trading activity"""
        log_entry = self._create_log_entry(
            "INFO",
            f"Trade: {action} {quantity} {ticker} @ ${price}",
            {
                "type": "trading",
                "action": action,
                "ticker": ticker,
                "quantity": quantity,
                "price": price,
                "order_id": order_id,
                **kwargs
            }
        )
        self._send_log(log_entry)

    def log_ai_request(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        duration_ms: float,
        **kwargs
    ):
        """Log AI/OpenAI request for cost tracking"""
        log_entry = self._create_log_entry(
            "INFO",
            f"AI Request: {model} - {prompt_tokens + completion_tokens} tokens (${cost:.4f})",
            {
                "type": "ai_request",
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "cost_usd": cost,
                "duration_ms": duration_ms,
                **kwargs
            }
        )
        self._send_log(log_entry)

    def log_database_query(
        self,
        query: str,
        duration_ms: float,
        rows_affected: int = 0,
        **kwargs
    ):
        """Log database query performance"""
        log_entry = self._create_log_entry(
            "INFO",
            f"DB Query: {duration_ms:.2f}ms - {rows_affected} rows",
            {
                "type": "database_query",
                "query": query[:200],  # Truncate long queries
                "duration_ms": duration_ms,
                "rows_affected": rows_affected,
                **kwargs
            }
        )
        self._send_log(log_entry)

    def log_cache_operation(
        self,
        operation: str,
        key: str,
        hit: bool = True,
        duration_ms: float = 0,
        **kwargs
    ):
        """Log cache operations (Redis)"""
        log_entry = self._create_log_entry(
            "INFO",
            f"Cache {operation}: {key} - {'HIT' if hit else 'MISS'}",
            {
                "type": "cache",
                "operation": operation,
                "key": key,
                "hit": hit,
                "duration_ms": duration_ms,
                **kwargs
            }
        )
        self._send_log(log_entry)

    def log_exception(self, exc: Exception, context: Optional[Dict[str, Any]] = None):
        """Log exception with traceback"""
        log_entry = self._create_log_entry(
            "ERROR",
            f"Exception: {str(exc)}",
            {
                "type": "exception",
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc(),
                "context": context or {}
            }
        )
        self._send_log(log_entry)

    def close(self):
        """Close connection to Logstash"""
        if self.socket:
            self.socket.close()


# Decorator for automatic API logging
def log_api_call(elk_logger: ELKLogger):
    """Decorator to automatically log API calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                # Extract request info from kwargs
                request = kwargs.get('request')
                if request:
                    elk_logger.log_api_request(
                        endpoint=request.url.path,
                        method=request.method,
                        status_code=200,
                        duration_ms=duration_ms
                    )

                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                request = kwargs.get('request')
                if request:
                    elk_logger.log_api_request(
                        endpoint=request.url.path,
                        method=request.method,
                        status_code=500,
                        duration_ms=duration_ms
                    )
                elk_logger.log_exception(e, context={"function": func.__name__})
                raise

        return wrapper
    return decorator


# Singleton instance
_elk_logger_instance: Optional[ELKLogger] = None


def get_elk_logger(
    service_name: str = "ai-trading-backend",
    logstash_host: str = "localhost",
    logstash_port: int = 5000
) -> ELKLogger:
    """Get or create ELK logger singleton"""
    global _elk_logger_instance
    if _elk_logger_instance is None:
        _elk_logger_instance = ELKLogger(
            service_name=service_name,
            logstash_host=logstash_host,
            logstash_port=logstash_port
        )
    return _elk_logger_instance
