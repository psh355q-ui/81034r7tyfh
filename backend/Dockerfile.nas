# Dockerfile for Synology NAS (optimized for ARM/x64)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi>=0.104.0 \
    uvicorn[standard]>=0.24.0 \
    pydantic>=2.5.0 \
    pydantic-settings>=2.1.0 \
    redis>=5.0.0 \
    pandas>=2.1.0 \
    numpy>=1.24.0 \
    yfinance>=0.2.32 \
    tenacity>=8.2.3 \
    prometheus-client>=0.19.0 \
    python-dotenv>=1.0.0 \
    httpx>=0.25.0 \
    alembic>=1.12.0 \
    psycopg2-binary>=2.9.9

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
