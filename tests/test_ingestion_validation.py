"""Verify raw-load validation, including null and malformed input cases."""

import unittest

from ingestion.load_activity import validate_row


class IngestionValidationTests(unittest.TestCase):
    def setUp(self):
        self.valid = ["101", "1383264000000", "39", "1.2", "", "0", "2", "3.5"]

    def test_allows_valid_rows_and_empty_measures(self):
        self.assertIsNone(validate_row(self.valid))

    def test_rejects_invalid_keys_and_bad_field_counts(self):
        for index, value in ((0, ""), (0, "10001"), (1, "-1"), (2, "unknown")):
            row = self.valid.copy()
            row[index] = value
            self.assertIsNotNone(validate_row(row))
        self.assertIsNotNone(validate_row(self.valid[:-1]))

    def test_rejects_invalid_negative_and_nonfinite_measures(self):
        for value in ("not-a-number", "-0.1", "NaN", "Infinity"):
            row = self.valid.copy()
            row[7] = value
            self.assertIsNotNone(validate_row(row))


if __name__ == "__main__":
    unittest.main()
