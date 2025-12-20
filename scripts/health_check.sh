#!/bin/bash
# Health Check Script

echo "🏥 Checking system health..."

# Check backend
if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Backend: Healthy"
else
    echo "❌ Backend: Unhealthy"
fi

# Check frontend
if curl -sf http://localhost:3002/health > /dev/null 2>&1; then
    echo "✅ Frontend: Healthy"  
else
    echo "❌ Frontend: Unhealthy"
fi

# Check PostgreSQL
if docker exec ai-trading-postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL: Healthy"
else
    echo "❌ PostgreSQL: Unhealthy"
fi

# Check Redis
if docker exec ai-trading-redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis: Healthy"
else
    echo "❌ Redis: Unhealthy"
fi
