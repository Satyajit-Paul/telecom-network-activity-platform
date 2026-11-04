"""Create an auditable, bounded sample from a checksum-verified source file."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def create_sample(source: Path, destination: Path, expected_md5: str, limit: int) -> dict:
    """Verify the whole source, then copy its first complete lines into a new file."""
    if limit < 1:
        raise ValueError("limit must be positive")
    if not re.fullmatch(r"[0-9a-fA-F]{32}", expected_md5):
        raise ValueError("expected_md5 must contain 32 hexadecimal characters")
    if source.resolve() == destination.resolve():
        raise ValueError("source and destination must be different files")
    metadata_path = destination.with_name(destination.name + ".provenance.json")
    if destination.exists() or metadata_path.exists():
        raise FileExistsError("Refusing to overwrite an existing sample or provenance file")
    initial_stat = source.stat()
    if initial_stat.st_size == 0:
        raise ValueError("source contains no rows")

    md5 = hashlib.md5(usedforsecurity=False)  # Publisher's integrity checksum, not a security signature.
    source_sha256 = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            md5.update(chunk)
            source_sha256.update(chunk)
    if md5.hexdigest().lower() != expected_md5.lower():
        raise ValueError("source does not match the publisher's MD5 checksum")
    verified_stat = source.stat()
    if (initial_stat.st_size, initial_stat.st_mtime_ns) != (verified_stat.st_size, verified_stat.st_mtime_ns):
        raise RuntimeError("source changed during checksum verification")

    destination.parent.mkdir(parents=True, exist_ok=True)
    sample_sha256 = hashlib.sha256()
    count = 0
    created_sample = False
    try:
        with source.open("rb") as reader, destination.open("xb") as writer:
            created_sample = True
            for line in reader:
                if count >= limit:
                    break
                writer.write(line)
                sample_sha256.update(line)
                count += 1
        final_stat = source.stat()
        if (verified_stat.st_size, verified_stat.st_mtime_ns) != (final_stat.st_size, final_stat.st_mtime_ns):
            raise RuntimeError("source changed while extracting the sample")
    except Exception:
        if created_sample:
            destination.unlink(missing_ok=True)
        raise
    metadata = {
        "source_file": source.name,
        "source_md5": md5.hexdigest(),
        "source_sha256": source_sha256.hexdigest(),
        "sample_sha256": sample_sha256.hexdigest(),
        "sample_rows": count,
        "sampling": "first complete lines; not a representative sample",
    }
    with metadata_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(metadata, handle, indent=2)
        handle.write("\n")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--expected-md5", required=True)
    parser.add_argument("--rows", type=int, default=50000)
    args = parser.parse_args()
    metadata = create_sample(args.source, args.destination, args.expected_md5, args.rows)
    print(f"Created {metadata['sample_rows']} source rows in {args.destination}")
    print(f"Sample SHA-256: {metadata['sample_sha256']}")


if __name__ == "__main__":
    main()
