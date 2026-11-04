"""Load headerless activity TSV batches into PostgreSQL's raw layer."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import warnings
from contextlib import closing
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg2
from psycopg2.extras import Json, execute_batch

INSERT_ACCEPTED = """INSERT INTO raw.activity_records
    (batch_id, line_number, source_fields) VALUES (%s, %s, %s)"""
INSERT_REJECTED = """INSERT INTO raw.rejected_records
    (batch_id, line_number, source_fields, reason) VALUES (%s, %s, %s, %s)"""


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_row(row: list[str]) -> str | None:
    """Return a rejection reason; leave empty activity measures untouched."""
    if len(row) != 8:
        return f"expected 8 fields, found {len(row)}"
    try:
        if not row[0].isdigit() or not 1 <= int(row[0]) <= 10000:
            return "square_id must be an integer between 1 and 10000"
        if not row[1].isdigit() or int(row[1]) <= 0:
            return "interval_start_ms must be a positive integer"
        if not row[2].isdigit():
            return "country_code must contain digits"
        for value in row[3:]:
            if value:
                number = Decimal(value)
                if not number.is_finite() or number < 0:
                    return "activity measures must be finite and non-negative"
    except (InvalidOperation, ValueError):
        return "invalid numeric value"
    return None


def _load_batch(path: Path, source_system: str, batch_size: int, digest: str) -> dict:
    batch_id = None
    with closing(psycopg2.connect()) as conn, conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO raw.ingestion_batches
                   (source_system, source_file, content_sha256, status)
                   VALUES (%s, %s, %s, 'processing')
                   ON CONFLICT (source_system, content_sha256) DO UPDATE
                   SET source_file = EXCLUDED.source_file, status = 'processing',
                       ingested_at = clock_timestamp(), completed_at = NULL,
                       rows_read = 0, rows_accepted = 0, rows_rejected = 0,
                       error_message = NULL
                   WHERE raw.ingestion_batches.status = 'failed'
                   RETURNING batch_id""",
                (source_system, path.name, digest),
            )
            inserted = cur.fetchone()
            if not inserted:
                cur.execute(
                    "SELECT batch_id, status FROM raw.ingestion_batches "
                    "WHERE source_system = %s AND content_sha256 = %s",
                    (source_system, digest),
                )
                existing = cur.fetchone()
                if existing and existing[1] == "succeeded":
                    return {"batch_id": existing[0], "status": "already_loaded"}
                raise RuntimeError("This batch is already being processed")
            batch_id = inserted[0]
            accepted, rejected = [], []
            count = {"read": 0, "accepted": 0, "rejected": 0}

            def flush() -> None:
                if accepted:
                    execute_batch(cur, INSERT_ACCEPTED, accepted, page_size=batch_size)
                    accepted.clear()
                if rejected:
                    execute_batch(cur, INSERT_REJECTED, rejected, page_size=batch_size)
                    rejected.clear()

            with path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.reader(handle, delimiter="\t", strict=True)
                for row in reader:
                    count["read"] += 1
                    reason = validate_row(row)
                    if reason:
                        rejected.append((batch_id, reader.line_num, Json(row), reason))
                        count["rejected"] += 1
                    else:
                        accepted.append((batch_id, reader.line_num, Json(row)))
                        count["accepted"] += 1
                    if len(accepted) + len(rejected) >= batch_size:
                        flush()
            flush()
            # Detect changes between hashing and reading before committing the load.
            if file_sha256(path) != digest:
                raise RuntimeError("Source file changed while it was being loaded")
            cur.execute(
                """UPDATE raw.ingestion_batches SET status = 'succeeded',
                   completed_at = clock_timestamp(), rows_read = %s,
                   rows_accepted = %s, rows_rejected = %s WHERE batch_id = %s""",
                (count["read"], count["accepted"], count["rejected"], batch_id),
            )
            return {"batch_id": batch_id, "status": "succeeded", **count}


def load_batch(path: Path, source_system: str, batch_size: int = 1000) -> dict:
    """Load once by checksum, recording failure only after a full rollback."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    digest = file_sha256(path)
    try:
        return _load_batch(path, source_system, batch_size, digest)
    except Exception as exc:
        try:
            with closing(psycopg2.connect()) as conn, conn, conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO raw.ingestion_batches
                       (source_system, source_file, content_sha256, status,
                        completed_at, error_message)
                       VALUES (%s, %s, %s, 'failed', clock_timestamp(), %s)
                       ON CONFLICT (source_system, content_sha256) DO UPDATE
                       SET status = 'failed', completed_at = clock_timestamp(),
                           error_message = EXCLUDED.error_message
                       WHERE raw.ingestion_batches.status = 'failed'""",
                    (source_system, path.name, digest, f"Batch failed: {type(exc).__name__}"),
                )
        except psycopg2.Error:
            warnings.warn("Could not record batch failure in PostgreSQL", stacklevel=2)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--source-system", required=True, choices=("synthetic", "telecom_italia_milan"))
    parser.add_argument("--batch-size", type=int, default=1000)
    args = parser.parse_args()
    if not os.environ.get("PGPASSWORD"):
        parser.error("Set PGPASSWORD in your environment before loading")
    result = load_batch(args.file, args.source_system, args.batch_size)
    print(", ".join(f"{key}={value}" for key, value in result.items()))


if __name__ == "__main__":
    main()
