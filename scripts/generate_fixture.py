"""Generate small, deterministic synthetic batches for pipeline development."""

from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import datetime, timezone
from pathlib import Path

COLUMNS = (
    "square_id", "interval_start_ms", "country_code", "sms_in", "sms_out",
    "call_in", "call_out", "internet",
)
FILENAMES = ("baseline.tsv", "late.tsv", "correction.tsv", "manifest.json")


def generate(output_dir: Path, seed: int = 42) -> None:
    """Write a replay fixture without replacing existing files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = [name for name in FILENAMES if (output_dir / name).exists()]
    if existing:
        raise FileExistsError(f"Refusing to overwrite existing files: {', '.join(existing)}")

    rng = random.Random(seed)
    start_ms = int(datetime(2013, 11, 1, tzinfo=timezone.utc).timestamp() * 1000)
    rows = []
    for square in (101, 102, 103):
        for interval in range(3):
            for country in (39, 44):
                measures = [f"{rng.uniform(0, 20):.3f}" for _ in range(4)]
                measures.append(f"{rng.uniform(0, 100):.3f}")
                rows.append([str(square), str(start_ms + interval * 600_000), str(country), *measures])

    late = rows.pop()  # One valid key arrives in a later batch.
    corrected = rows[0].copy()
    corrected[-1] = f"{float(corrected[-1]) + 10:.3f}"
    missing_key = rows[1].copy()
    missing_key[0] = ""
    negative_measure = rows[2].copy()
    negative_measure[3] = "-1.000"
    invalid_number = rows[3].copy()
    invalid_number[7] = "not-a-number"
    malformed = rows[4][:-1]
    baseline = rows + [rows[0].copy(), missing_key, negative_measure, invalid_number, malformed]

    for name, batch in (("baseline.tsv", baseline), ("late.tsv", [late]),
                        ("correction.tsv", [corrected])):
        with (output_dir / name).open("x", encoding="utf-8", newline="") as handle:
            csv.writer(handle, delimiter="\t", lineterminator="\n").writerows(batch)

    manifest = {
        "synthetic": True,
        "seed": seed,
        "columns": COLUMNS,
        "interval_minutes": 10,
        "counts": {"baseline": len(baseline), "late": 1, "correction": 1},
        "scenarios": {
            "duplicate_key": rows[0][:3],
            "late_key": late[:3],
            "correction_key": corrected[:3],
            "invalid_rows": ["missing_square_id", "negative_sms_in", "invalid_internet", "missing_column"],
        },
    }
    with (output_dir / "manifest.json").open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    generate(args.output_dir, args.seed)
    print(f"Generated synthetic fixture in {args.output_dir}")


if __name__ == "__main__":
    main()

