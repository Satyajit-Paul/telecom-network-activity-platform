CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.ingestion_batches (
    batch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_system TEXT NOT NULL,
    source_file TEXT NOT NULL,
    content_sha256 CHAR(64) NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('processing', 'succeeded', 'failed')),
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    completed_at TIMESTAMPTZ,
    rows_read BIGINT NOT NULL DEFAULT 0,
    rows_accepted BIGINT NOT NULL DEFAULT 0,
    rows_rejected BIGINT NOT NULL DEFAULT 0,
    error_message TEXT,
    UNIQUE (source_system, content_sha256)
);

-- Preserve fields as received. Typing and key-level deduplication belong in dbt.
CREATE TABLE IF NOT EXISTS raw.activity_records (
    batch_id BIGINT NOT NULL REFERENCES raw.ingestion_batches(batch_id),
    line_number BIGINT NOT NULL,
    source_fields JSONB NOT NULL,
    PRIMARY KEY (batch_id, line_number)
);

CREATE TABLE IF NOT EXISTS raw.rejected_records (
    batch_id BIGINT NOT NULL REFERENCES raw.ingestion_batches(batch_id),
    line_number BIGINT NOT NULL,
    source_fields JSONB NOT NULL,
    reason TEXT NOT NULL,
    PRIMARY KEY (batch_id, line_number)
);
