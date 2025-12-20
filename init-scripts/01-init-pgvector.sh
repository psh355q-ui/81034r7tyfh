#!/bin/bash
set -e

# This script runs on first container startup
# Location: /docker-entrypoint-initdb.d/01-init-pgvector.sh

echo "🚀 Initializing TimescaleDB with pgvector extension..."

# Install pgvector extension
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create pgvector extension
    CREATE EXTENSION IF NOT EXISTS vector;
    
    -- Verify installation
    SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
EOSQL

echo "✅ pgvector extension installed successfully"

# Create TimescaleDB extension
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create TimescaleDB extension
    CREATE EXTENSION IF NOT EXISTS timescaledb;
    
    -- Verify installation
    SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';
EOSQL

echo "✅ TimescaleDB extension verified"

# Create initial schema for vector store
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Main vector storage table
    CREATE TABLE IF NOT EXISTS document_embeddings (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(20) NOT NULL,
        doc_type VARCHAR(50) NOT NULL,
        content TEXT NOT NULL,
        content_hash VARCHAR(64) UNIQUE,
        embedding VECTOR(1536) NOT NULL,
        metadata JSONB NOT NULL DEFAULT '{}',
        document_date TIMESTAMPTZ NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        
        CONSTRAINT valid_doc_type CHECK (doc_type IN ('10K', '10Q', '8K', 'news', 'earnings_call', 'regime'))
    );

    -- Convert to hypertable (use document_date for partitioning)
    SELECT create_hypertable('document_embeddings', 'document_date',
        chunk_time_interval => INTERVAL '3 months',
        if_not_exists => TRUE
    );

    -- Vector similarity index (IVFFlat algorithm)
    CREATE INDEX IF NOT EXISTS idx_embedding_ivfflat ON document_embeddings 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

    -- Lookup indexes
    CREATE INDEX IF NOT EXISTS idx_doc_ticker_type ON document_embeddings(ticker, doc_type);
    CREATE INDEX IF NOT EXISTS idx_doc_hash ON document_embeddings(content_hash);
    CREATE INDEX IF NOT EXISTS idx_doc_date ON document_embeddings(document_date DESC);
    CREATE INDEX IF NOT EXISTS idx_doc_created ON document_embeddings(created_at DESC);

    -- Auto-generated tags table
    CREATE TABLE IF NOT EXISTS document_tags (
        id SERIAL PRIMARY KEY,
        document_id INTEGER NOT NULL REFERENCES document_embeddings(id) ON DELETE CASCADE,
        tag_type VARCHAR(50) NOT NULL,
        tag_value VARCHAR(200) NOT NULL,
        confidence FLOAT NOT NULL DEFAULT 1.0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        
        UNIQUE(document_id, tag_type, tag_value),
        CONSTRAINT valid_tag_type CHECK (tag_type IN ('ticker', 'sector', 'topic', 'entity', 'geographic'))
    );

    -- Indexes for tag-based search
    CREATE INDEX IF NOT EXISTS idx_tag_type_value ON document_tags(tag_type, tag_value);
    CREATE INDEX IF NOT EXISTS idx_tag_document ON document_tags(document_id);

    -- Materialized view for tag statistics
    CREATE MATERIALIZED VIEW IF NOT EXISTS tag_stats AS
    SELECT 
        tag_type,
        tag_value,
        COUNT(DISTINCT document_id) as doc_count,
        AVG(confidence) as avg_confidence,
        MAX(de.created_at) as last_seen
    FROM document_tags dt
    JOIN document_embeddings de ON dt.document_id = de.id
    GROUP BY tag_type, tag_value;

    CREATE INDEX IF NOT EXISTS idx_tag_stats_lookup ON tag_stats(tag_type, tag_value);

    -- Incremental update tracking table
    CREATE TABLE IF NOT EXISTS document_sync_status (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(20) NOT NULL,
        doc_type VARCHAR(50) NOT NULL,
        last_sync_date TIMESTAMPTZ NOT NULL,
        last_document_date TIMESTAMPTZ NOT NULL,
        documents_processed INTEGER NOT NULL DEFAULT 0,
        total_cost_usd DECIMAL(10, 6) NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        
        UNIQUE(ticker, doc_type)
    );

    CREATE INDEX IF NOT EXISTS idx_sync_status_lookup ON document_sync_status(ticker, doc_type);

    -- Embedding cost tracking
    CREATE TABLE IF NOT EXISTS embedding_costs (
        id SERIAL PRIMARY KEY,
        batch_id UUID NOT NULL,
        doc_count INTEGER NOT NULL,
        total_tokens INTEGER NOT NULL,
        cost_usd DECIMAL(10, 6) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    SELECT create_hypertable('embedding_costs', 'created_at',
        chunk_time_interval => INTERVAL '1 month',
        if_not_exists => TRUE
    );
EOSQL

echo "✅ Vector store schema created successfully"

# Create features table for Feature Store (existing from Phase 1)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS features (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(20) NOT NULL,
        feature_name VARCHAR(50) NOT NULL,
        value DOUBLE PRECISION,
        as_of_timestamp TIMESTAMPTZ NOT NULL,
        calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        version INTEGER DEFAULT 1,
        metadata JSONB,
        UNIQUE(ticker, feature_name, as_of_timestamp, version)
    );

    SELECT create_hypertable('features', 'as_of_timestamp',
        chunk_time_interval => INTERVAL '1 month',
        if_not_exists => TRUE
    );

    CREATE INDEX IF NOT EXISTS idx_features_lookup ON features(ticker, feature_name, as_of_timestamp DESC);
EOSQL

echo "✅ Features table created successfully"

# Grant permissions
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
EOSQL

echo "✅ Database initialization complete!"
echo ""
echo "📊 Created tables:"
echo "  - document_embeddings (with pgvector)"
echo "  - document_tags"
echo "  - tag_stats (materialized view)"
echo "  - document_sync_status"
echo "  - embedding_costs"
echo "  - features (existing)"
echo ""
echo "🔍 Verify installation:"
echo "  docker exec -it ai-trading-timescaledb psql -U postgres -d ai_trading -c \"SELECT * FROM pg_extension WHERE extname IN ('vector', 'timescaledb');\""
