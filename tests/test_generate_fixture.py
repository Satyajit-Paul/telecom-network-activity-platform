"""Verify fixture scenarios and reproducibility without external dependencies."""

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from generate_fixture import FILENAMES, generate  # noqa: E402


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle, delimiter="\t"))


class FixtureTests(unittest.TestCase):
    def test_is_deterministic_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / "first", Path(tmp) / "second"
            generate(first)
            generate(second)
            for name in FILENAMES:
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())
            with self.assertRaises(FileExistsError):
                generate(first)

    def test_replay_scenarios_have_expected_keys_and_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generate(root)
            manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
            baseline = read_rows(root / "baseline.tsv")
            late = read_rows(root / "late.tsv")[0]
            corrected = read_rows(root / "correction.tsv")[0]
            self.assertTrue(manifest["synthetic"])
            self.assertEqual(len(baseline), manifest["counts"]["baseline"])
            self.assertEqual(sum(row == baseline[0] for row in baseline), 2)
            self.assertNotIn(late[:3], [row[:3] for row in baseline])
            self.assertEqual(corrected[:3], baseline[0][:3])
            self.assertNotEqual(corrected[-1], baseline[0][-1])
            self.assertTrue(any(not row[0] for row in baseline))
            self.assertTrue(any(len(row) == 7 for row in baseline))
            self.assertTrue(any(len(row) == 8 and row[3] == "-1.000" for row in baseline))
            self.assertTrue(any(len(row) == 8 and row[7] == "not-a-number" for row in baseline))


if __name__ == "__main__":
    unittest.main()
