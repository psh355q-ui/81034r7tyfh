-- data_collection_progress 테이블 생성/업데이트 SQL
-- postgres-prod 컨테이너에서 직접 실행

-- 1. 테이블이 없으면 생성
CREATE TABLE IF NOT EXISTS data_collection_progress (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(100),
    source VARCHAR(50) NOT NULL,
    collection_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    progress_pct FLOAT NOT NULL DEFAULT 0.0,
    items_processed INTEGER NOT NULL DEFAULT 0,
    items_total INTEGER,
    error_message TEXT,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    job_metadata JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 2. 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_data_collection_source ON data_collection_progress (source);

CREATE INDEX IF NOT EXISTS idx_data_collection_type ON data_collection_progress (collection_type);

CREATE INDEX IF NOT EXISTS idx_data_collection_status ON data_collection_progress (status);

CREATE INDEX IF NOT EXISTS idx_data_collection_task_name ON data_collection_progress (task_name);

-- 3. 업데이트 함수 (자동 updated_at)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 4. 트리거 생성
DROP TRIGGER IF NOT EXISTS update_data_collection_progress_updated_at ON data_collection_progress;

CREATE TRIGGER update_data_collection_progress_updated_at
    BEFORE UPDATE ON data_collection_progress
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 확인
SELECT 'Table created successfully!' as status;

\dt data_collection_progress