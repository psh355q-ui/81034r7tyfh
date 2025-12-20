-- Knowledge Graph Database Initialization for Phase 14 Deep Reasoning
-- PostgreSQL + pgvector

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create relationships table
CREATE TABLE IF NOT EXISTS relationships (
    id SERIAL PRIMARY KEY,
    subject VARCHAR(255) NOT NULL,
    relation VARCHAR(100) NOT NULL,
    object VARCHAR(255) NOT NULL,
    evidence_text TEXT,
    source VARCHAR(255),
    date DATE,
    embedding vector(1536),
    confidence FLOAT DEFAULT 0.8,
    verified_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(subject, relation, object)
);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_relationships_subject ON relationships(subject);
CREATE INDEX IF NOT EXISTS idx_relationships_object ON relationships(object);
CREATE INDEX IF NOT EXISTS idx_relationships_relation ON relationships(relation);
CREATE INDEX IF NOT EXISTS idx_relationships_is_active ON relationships(is_active);
CREATE INDEX IF NOT EXISTS idx_relationships_confidence ON relationships(confidence DESC);

-- Create vector index (HNSW) for embedding similarity search
CREATE INDEX IF NOT EXISTS idx_relationships_embedding
ON relationships
USING hnsw (embedding vector_cosine_ops);

-- Create entities table (for embedding search)
CREATE TABLE IF NOT EXISTS entities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    entity_type VARCHAR(50),
    description TEXT,
    embedding vector(1536),  -- OpenAI text-embedding-3-small dimension
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS idx_entities_embedding ON entities
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create evidence table (for storing verification results)
CREATE TABLE IF NOT EXISTS evidence (
    id SERIAL PRIMARY KEY,
    relationship_id INTEGER REFERENCES relationships(id) ON DELETE CASCADE,
    evidence_type VARCHAR(50),  -- 'news', 'web_search', 'sec_filing', etc.
    evidence_text TEXT,
    source_url TEXT,
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evidence_relationship_id ON evidence(relationship_id);

-- Insert seed knowledge from config_phase14.py
INSERT INTO relationships (subject, relation, object, confidence, evidence_text) VALUES
    ('Google', 'partner', 'Broadcom', 0.95, 'TPU chip design partnership'),
    ('Broadcom', 'chip_designer', 'Google', 0.95, 'Designs Google TPU chips'),
    ('Google', 'competitor', 'Nvidia', 0.90, 'Custom AI chips vs GPUs'),
    ('Google', 'competitor', 'OpenAI', 0.85, 'AI model development'),
    ('Google', 'competitor', 'Microsoft', 0.85, 'Cloud AI services'),
    ('Google', 'competitor', 'Meta', 0.80, 'AI research'),
    ('Broadcom', 'partner', 'Meta', 0.85, 'MTIA chip design'),
    ('Broadcom', 'partner', 'Apple', 0.90, 'Custom chip design'),
    ('Broadcom', 'competitor', 'Marvell', 0.75, 'ASIC design market'),
    ('Nvidia', 'competitor', 'AMD', 0.95, 'GPU market'),
    ('Nvidia', 'competitor', 'Intel', 0.85, 'Data center chips'),
    ('OpenAI', 'partner', 'Microsoft', 0.95, 'Azure AI infrastructure'),
    ('OpenAI', 'investor', 'Microsoft', 0.95, 'Major investment'),
    ('OpenAI', 'investor', 'SoftBank', 0.90, 'Investment partnership'),
    ('Samsung', 'competitor', 'SK Hynix', 0.95, 'HBM memory market'),
    ('Samsung', 'competitor', 'Micron', 0.90, 'Memory chip market'),
    ('Samsung', 'competitor', 'TSMC', 0.85, 'Foundry business')
ON CONFLICT (subject, relation, object) DO NOTHING;

-- Insert entity data
INSERT INTO entities (name, entity_type, description) VALUES
    ('Google', 'company', 'Full-stack AI company with custom TPU chips, Gemini models, and cloud services'),
    ('Broadcom', 'company', 'ASIC/TPU chip designer, hidden beneficiary of custom AI chip trend'),
    ('Nvidia', 'company', 'GPU market leader with CUDA ecosystem, facing long-term custom chip risk'),
    ('OpenAI', 'company', 'AI research lab, ChatGPT/GPT-4 creator, partnered with Microsoft'),
    ('Microsoft', 'company', 'Cloud provider with Azure AI, OpenAI investor, developing custom Maia chips'),
    ('Amazon', 'company', 'AWS cloud provider with Trainium/Inferentia custom AI chips'),
    ('Samsung', 'company', 'Memory and foundry, HBM supplier, 2nm process development'),
    ('SK Hynix', 'company', 'HBM3/HBM3E market leader, Nvidia''s primary HBM supplier'),
    ('Meta', 'company', 'AI research with MTIA custom chips, Broadcom partnership'),
    ('Apple', 'company', 'Custom chip leader with M-series, Broadcom partnership')
ON CONFLICT (name) DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for auto-updating updated_at
CREATE TRIGGER update_relationships_updated_at BEFORE UPDATE ON relationships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_entities_updated_at BEFORE UPDATE ON entities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
