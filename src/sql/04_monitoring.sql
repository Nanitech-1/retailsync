-- ==============================================================================
-- 04_monitoring.sql: Pipeline Health and Run Audit Tables
-- ==============================================================================

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id VARCHAR(64) PRIMARY KEY,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    status VARCHAR(32) NOT NULL,
    rows_ingested INTEGER DEFAULT 0,
    rows_rejected INTEGER DEFAULT 0,
    rows_loaded INTEGER DEFAULT 0,
    llm_calls INTEGER DEFAULT 0,
    llm_failures INTEGER DEFAULT 0,
    quality_score NUMERIC(5, 2) DEFAULT 100.0,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started ON pipeline_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status);
