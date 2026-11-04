"""Opt-in end-to-end checks against a built warehouse and loaded fixtures."""

import os
import unittest
from contextlib import closing

import psycopg2
from psycopg2 import sql


@unittest.skipUnless(os.getenv("RUN_DBT_TESTS") == "1", "set RUN_DBT_TESTS=1 for warehouse integration tests")
class WarehouseTests(unittest.TestCase):
    def test_synthetic_correction_wins_over_baseline(self):
        with closing(psycopg2.connect()) as conn, conn.cursor() as cur:
            cur.execute(
                """SELECT b.source_file, (r.source_fields ->> 7)::numeric
                   FROM raw.activity_records r
                   JOIN raw.ingestion_batches b USING (batch_id)
                   WHERE b.source_system = 'synthetic'
                     AND b.source_file IN ('baseline.tsv', 'correction.tsv')
                     AND r.source_fields ->> 0 = '101'
                     AND r.source_fields ->> 1 = '1383264000000'
                     AND r.source_fields ->> 2 = '39'
                   ORDER BY b.batch_id, r.line_number"""
            )
            source_rows = cur.fetchall()
            baseline = [value for name, value in source_rows if name == "baseline.tsv"]
            correction = [value for name, value in source_rows if name == "correction.tsv"]
            self.assertTrue(baseline, "Load the default synthetic baseline fixture first")
            self.assertEqual(len(correction), 1, "Load the default synthetic correction fixture first")
            self.assertNotEqual(baseline[0], correction[0])
            core = sql.Identifier(f"{os.getenv('DBT_SCHEMA', 'telecom')}_core")
            cur.execute(
                sql.SQL("""SELECT b.source_file, f.internet_activity
                   FROM {}.fct_grid_activity f
                   JOIN {}.dim_grid g USING (grid_key)
                   JOIN {}.dim_country c USING (country_key)
                   JOIN raw.ingestion_batches b ON b.batch_id = f.source_batch_id
                   WHERE f.source_system = 'synthetic' AND g.square_id = 101
                     AND f.interval_start_ms = 1383264000000 AND c.country_code = '39'""").format(core, core, core)
            )
            self.assertEqual(cur.fetchall(), [("correction.tsv", correction[0])])

    def test_real_source_blank_is_null_not_zero(self):
        with closing(psycopg2.connect()) as conn, conn.cursor() as cur:
            core = sql.Identifier(f"{os.getenv('DBT_SCHEMA', 'telecom')}_core")
            cur.execute(
                sql.SQL("""SELECT count(*)
                   FROM {}.fct_grid_activity f
                   JOIN raw.activity_records r
                     ON f.source_batch_id = r.batch_id AND f.source_line_number = r.line_number
                   WHERE f.source_system = 'telecom_italia_milan'
                     AND r.source_fields ->> 7 = '' AND f.internet_activity IS NULL""").format(core)
            )
            self.assertGreater(cur.fetchone()[0], 0, "Load the documented real-data sample first")


if __name__ == "__main__":
    unittest.main()
