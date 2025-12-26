"""
Logging Decorator for Agent Endpoints

Simple, explicit decorator to add logging to any endpoint.
No hidden magic, clear and debuggable.

Usage:
    @router.post("/endpoint")
    @log_endpoint("agent-name", "category")
    async def my_endpoint(request):
        return result
"""

from functools import wraps
from datetime import datetime
import traceback
from typing import Callable, Any
import inspect

from backend.ai.skills.common.agent_logger import AgentLogger
from backend.ai.skills.common.log_schema import (
    ExecutionLog,
    ErrorLog,
    ExecutionStatus,
    ErrorImpact
)


def log_endpoint(agent_name: str, category: str = "system", impact: ErrorImpact = ErrorImpact.MEDIUM):
    """
    Decorator to add logging to any endpoint
    
    Args:
        agent_name: Name of the agent (e.g., "signal-consolidation")
        category: Category (system, analysis, war-room, trading)
        impact: Default error impact level
    
    Example:
        @router.post("/consolidate")
        @log_endpoint("signal-consolidation", "system")
        async def consolidate_signals(request: Request):
            # Your business logic here
            return result
    """
    def decorator(func: Callable) -> Callable:
        # Create logger once per function
        logger = AgentLogger(agent_name, category)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = datetime.now()
            task_id = f"{agent_name}-{start_time.strftime('%Y%m%d-%H%M%S-%f')[:20]}"
            
            # Extract request info if available
            request_info = {}
            for arg in args:
                if hasattr(arg, 'dict'):  # Pydantic model
                    try:
                        request_info = arg.dict()
                        break
                    except:
                        pass
            
            try:
                # Execute endpoint
                result = await func(*args, **kwargs)
                
                # Extract result info
                result_info = {}
                if hasattr(result, 'dict'):
                    try:
                        result_info = result.dict()
                    except:
                        result_info = {"type": str(type(result).__name__)}
                elif isinstance(result, dict):
                    result_info = result
                else:
                    result_info = {"type": str(type(result).__name__)}
                
                # Log success
                logger.log_execution(ExecutionLog(
                    timestamp=datetime.now(),
                    agent=f"{category}/{agent_name}",
                    task_id=task_id,
                    status=ExecutionStatus.SUCCESS,
                    duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    input=request_info or {"args_count": len(args), "kwargs_count": len(kwargs)},
                    output=result_info
                ))
                
                return result
                
            except Exception as e:
                # Log error
                logger.log_error(ErrorLog(
                    timestamp=datetime.now(),
                    agent=f"{category}/{agent_name}",
                    task_id=task_id,
                    error={
                        "type": type(e).__name__,
                        "message": str(e),
                        "stack": traceback.format_exc(),
                        "context": request_info or {"function": func.__name__}
                    },
                    impact=impact,
                    recovery_attempted=False
                ))
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = datetime.now()
            task_id = f"{agent_name}-{start_time.strftime('%Y%m%d-%H%M%S-%f')[:20]}"
            
            # Extract request info
            request_info = {}
            for arg in args:
                if hasattr(arg, 'dict'):
                    try:
                        request_info = arg.dict()
                        break
                    except:
                        pass
            
            try:
                # Execute endpoint
                result = func(*args, **kwargs)
                
                # Extract result info
                result_info = {}
                if hasattr(result, 'dict'):
                    try:
                        result_info = result.dict()
                    except:
                        result_info = {"type": str(type(result).__name__)}
                elif isinstance(result, dict):
                    result_info = result
                else:
                    result_info = {"type": str(type(result).__name__)}
                
                # Log success
                logger.log_execution(ExecutionLog(
                    timestamp=datetime.now(),
                    agent=f"{category}/{agent_name}",
                    task_id=task_id,
                    status=ExecutionStatus.SUCCESS,
                    duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    input=request_info or {"args_count": len(args), "kwargs_count": len(kwargs)},
                    output=result_info
                ))
                
                return result
                
            except Exception as e:
                # Log error
                logger.log_error(ErrorLog(
                    timestamp=datetime.now(),
                    agent=f"{category}/{agent_name}",
                    task_id=task_id,
                    error={
                        "type": type(e).__name__,
                        "message": str(e),
                        "stack": traceback.format_exc(),
                        "context": request_info or {"function": func.__name__}
                    },
                    impact=impact,
                    recovery_attempted=False
                ))
                raise
        
        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
