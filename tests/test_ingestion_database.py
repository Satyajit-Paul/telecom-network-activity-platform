"""Opt-in integration checks against the local project database."""

import csv
import os
import tempfile
import unittest
import uuid
from pathlib import Path

import psycopg2

from ingestion.load_activity import load_batch
from scripts.generate_fixture import generate


@unittest.skipUnless(os.getenv("RUN_DB_TESTS") == "1", "set RUN_DB_TESTS=1 for PostgreSQL integration tests")
class IngestionDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.source = f"integration_test_{uuid.uuid4().hex}"
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        generate(self.root)

    def tearDown(self):
        # Remove only records created under this test's random source identifier.
        with psycopg2.connect() as conn, conn.cursor() as cur:
            for table in ("rejected_records", "activity_records"):
                cur.execute(
                    f"DELETE FROM raw.{table} WHERE batch_id IN "
                    "(SELECT batch_id FROM raw.ingestion_batches WHERE source_system = %s)",
                    (self.source,),
                )
            cur.execute("DELETE FROM raw.ingestion_batches WHERE source_system = %s", (self.source,))
        self.temp.cleanup()

    def test_load_replay_and_rollback(self):
        first = load_batch(self.root / "baseline.tsv", self.source, batch_size=2)
        self.assertEqual((first["read"], first["accepted"], first["rejected"]), (22, 18, 4))
        repeated = load_batch(self.root / "baseline.tsv", self.source, batch_size=2)
        self.assertEqual(repeated, {"batch_id": first["batch_id"], "status": "already_loaded"})
        self.assertEqual(load_batch(self.root / "late.tsv", self.source)["accepted"], 1)
        self.assertEqual(load_batch(self.root / "correction.tsv", self.source)["accepted"], 1)

        broken = self.root / "broken.tsv"
        broken.write_text('101\t1383264000000\t39\t1\t2\t3\t4\t5\n"unterminated\n', encoding="utf-8")
        with self.assertRaises(csv.Error):
            load_batch(broken, self.source, batch_size=1)

        with psycopg2.connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT status, rows_read, rows_accepted, rows_rejected FROM raw.ingestion_batches WHERE source_system = %s ORDER BY batch_id", (self.source,))
            batches = cur.fetchall()
            self.assertEqual([row[0] for row in batches], ["succeeded", "succeeded", "succeeded", "failed"])
            self.assertEqual(batches[0][1:], (22, 18, 4))
            cur.execute("SELECT count(*) FROM raw.activity_records a JOIN raw.ingestion_batches b USING (batch_id) WHERE b.source_system = %s", (self.source,))
            self.assertEqual(cur.fetchone()[0], 20)
            cur.execute("SELECT count(*) FROM raw.rejected_records r JOIN raw.ingestion_batches b USING (batch_id) WHERE b.source_system = %s", (self.source,))
            self.assertEqual(cur.fetchone()[0], 4)


if __name__ == "__main__":
    unittest.main()
