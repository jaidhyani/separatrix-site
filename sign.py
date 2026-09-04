#!/usr/bin/env python3
"""sign.py — append a signature to the Separatrix signatory roster.

Since v1.2 the signatures live outside the hashed text: a new signatory is a
record in src/signatories.json, not a version bump. A record is a dated
statement that this person signed one exact issued text, so it carries the
sha256 of the bytes signed.

    ./sign.py --name "Jai Dhyani" --version v1.2 [--role "…"] [--statement "…"]

The hashes come from commitment/history/versions.json when the version is
already issued there, and otherwise from src/*.md — the bytes about to be
issued under that version. If both exist and disagree, this refuses: the
signer is looking at src/, so signing a manifest hash that src no longer
matches would record a signature over bytes nobody read.

Writes src/signatories.json only. Run ./build-commitment.py afterwards to
re-render /commitment/signatories/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent
SOURCE = REPO / "src" / "signatories.json"
MANIFEST = REPO / "commitment" / "history" / "versions.json"
PARTS = ("commitment", "details")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes_for(version: str) -> dict[str, str]:
    live = {p: digest(REPO / "src" / f"{p}.md") for p in PARTS}
    issued = next(
        (v["sha256"] for v in json.loads(MANIFEST.read_text()) if v["version"] == version),
        None,
    )
    if issued is None:
        return live
    if issued != live:
        raise SystemExit(
            f"REFUSING to sign {version}: the issued hashes in versions.json do not "
            f"match src/ as it stands now.\n"
            f"  issued: {issued}\n"
            f"  src/:   {live}\n"
            f"Check out the bytes being signed (or bump the version) and re-run."
        )
    return issued


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--name", required=True, help="the signer, as they wish to be listed")
    ap.add_argument("--version", required=True, help="the version signed, e.g. v1.2")
    ap.add_argument("--date", default=date.today().isoformat(), help="date of signature")
    ap.add_argument("--role", default="", help='e.g. "for Separatrix, and personally"')
    ap.add_argument("--note", default="", help="one line of context for this record")
    ap.add_argument("--statement", default="", help="the signer's own words, recorded verbatim")
    args = ap.parse_args()

    registry = json.loads(SOURCE.read_text())
    records = registry["records"]

    if any(r["name"] == args.name and r["version"] == args.version for r in records):
        raise SystemExit(
            f"{args.name} already has a record for {args.version} — a signature is "
            f"recorded once; edit src/signatories.json by hand to correct one."
        )

    record = {"name": args.name}
    if args.role:
        record["role"] = args.role
    record["date"] = args.date
    record["version"] = args.version
    record["sha256"] = hashes_for(args.version)
    if args.note:
        record["note"] = args.note
    if args.statement:
        record["statement"] = args.statement

    records.append(record)
    SOURCE.write_text(json.dumps(registry, indent=2) + "\n")

    print(json.dumps(record, indent=2))
    print(f"\nwritten to {SOURCE.relative_to(REPO)} — run ./build-commitment.py to publish", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
