"""
Standalone test to generate and read logs without API server

Simulates signal consolidation agent behavior
"""

from datetime import datetime
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from backend.ai.skills.common.agent_logger import AgentLogger
from backend.ai.skills.common.log_schema import (
    ExecutionLog,
    ErrorLog,
    PerformanceLog,
    ExecutionStatus,
    ErrorImpact,
    AgentMetadata
)

print("="  * 70)
print("Agent Logging Simulation Test")
print("=" * 70)

# Create logger
logger = AgentLogger("signal-consolidation", "system")

# Test 1: Generate execution logs
print("\n📝 Test 1: Generate execution logs...")
for i in range(3):
    task_id = f"task-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{i}"
    
    exec_log = ExecutionLog(
        timestamp=datetime.now(),
        agent="system/signal-consolidation",
        task_id=task_id,
        status=ExecutionStatus.SUCCESS,
        duration_ms=800 + (i * 200),
        input={
            "ticker": ["AAPL", "MSFT", "GOOGL"][i],
            "hours": 24,
            "limit": 10
        },
        output={
            "total_count": 5 + i,
            "sources": ["war_room", "deep_reasoning"]
        }
    )
    
    logger.log_execution(exec_log)
    print(f"   ✅ Execution log {i+1}: {task_id}")

# Test 2: Generate error log
print("\n❌ Test 2: Generate error log...")
error_log = ErrorLog(
    timestamp=datetime.now(),
    agent="system/signal-consolidation",
    task_id=f"task-error-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
    error={
        "type": "DatabaseError",
        "message": "Connection timeout",
        "stack": "Traceback (simulated)...",
        "context": {"database": "postgresql", "timeout": "30s"}
    },
    impact=ErrorImpact.HIGH,
    recovery_attempted=False
)

logger.log_error(error_log)
print(f"   ✅ Error log generated")

# Test 3: Generate performance log
print("\n📊 Test 3: Generate performance log...")
perf_log = PerformanceLog(
    timestamp=datetime.now(),
    agent="system/signal-consolidation",
    metrics={
        "cpu_percent": 35.2,
        "memory_mb": 256,
        "api_calls": 2,
        "db_queries": 3,
        "avg_response_time_ms": 850
    }
)

logger.log_performance(perf_log)
print(f"   ✅ Performance log generated")

# Test 4: Create metadata
print("\n📋 Test 4: Create agent metadata...")
metadata = AgentMetadata(
    agent_name="signal-consolidation",
    category="system",
    version="1.0",
    dependencies=["database", "trading_signals"],
    performance_baseline={
        "avg_execution_time_ms": 1000,
        "p95_execution_time_ms": 2000,
        "success_rate": 0.98,
        "error_rate": 0.02
    },
    last_updated=datetime.now()
)

logger.update_metadata(metadata)
print(f"   ✅ Metadata created")

# Test 5: Read logs
print("\n📖 Test 5: Read logs...")
executions = logger.read_recent_executions(days=1)
errors = logger.read_recent_errors(days=1)

print(f"   Found {len(executions)} execution logs")
print(f"   Found {len(errors)} error logs")

# Test 6: Display logs
if executions:
    print("\n🔍 Test 6: Latest execution log:")
    latest = executions[-1]
    print(f"   Task ID: {latest['task_id']}")
    print(f"   Status: {latest['status']}")
    print(f"   Duration: {latest['duration_ms']}ms")
    print(f"   Input: {latest['input']}")
    print(f"   Output: {latest['output']}")

if errors:
    print("\n🔍 Test 7: Latest error log:")
    latest_error = errors[-1]
    print(f"   Task ID: {latest_error['task_id']}")
    print(f"   Error Type: {latest_error['error']['type']}")
    print(f"   Message: {latest_error['error']['message']}")
    print(f"   Impact: {latest_error['impact']}")

# Test 7: Verify metadata
print("\n🔍 Test 8: Verify metadata:")
saved_metadata = logger.get_metadata()
if saved_metadata:
    print(f"   Agent: {saved_metadata.agent_name}")
    print(f"   Category: {saved_metadata.category}")
    print(f"   Version: {saved_metadata.version}")
    print(f"   Dependencies: {', '.join(saved_metadata.dependencies)}")
    print(f"   Baselines: {list(saved_metadata.performance_baseline.keys())}")
else:
    print(f"   ❌ Failed to read metadata")

print("\n" + "=" * 70)
print("✅ All tests passed!")
print("=" * 70)

print(f"\n📁 Log files location:")
print(f"   {logger.log_dir}")
print(f"\n   execution-{datetime.now().date()}.jsonl")
print(f"   errors-{datetime.now().date()}.jsonl")
print(f"   performance-{datetime.now().date()}.jsonl")
print(f"   metadata.json")
