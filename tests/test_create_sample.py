"""Verify provenance, bounds, and safe failure behavior of sampling."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.create_sample import create_sample


class SampleTests(unittest.TestCase):
    def test_verified_bounded_sample_and_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, output = root / "source.tsv", root / "sample.tsv"
            source.write_bytes(b"one\ntwo\nthree\n")
            expected = hashlib.md5(source.read_bytes(), usedforsecurity=False).hexdigest()
            result = create_sample(source, output, expected, 2)
            self.assertEqual(output.read_bytes(), b"one\ntwo\n")
            self.assertEqual(result["sample_rows"], 2)
            self.assertEqual(result["sample_sha256"], hashlib.sha256(output.read_bytes()).hexdigest())
            metadata = json.loads((root / "sample.tsv.provenance.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata, result)
            with self.assertRaises(FileExistsError):
                create_sample(source, output, expected, 2)

    def test_checksum_mismatch_does_not_create_a_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, output = root / "source.tsv", root / "sample.tsv"
            source.write_bytes(b"not the expected source\n")
            with self.assertRaises(ValueError):
                create_sample(source, output, "0" * 32, 5)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
