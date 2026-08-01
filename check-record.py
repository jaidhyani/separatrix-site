#!/usr/bin/env python3
"""check-record.py — the public record's own consistency check.

Run before every push (build-commitment.py runs it automatically). Exits
nonzero, loudly, if the published record is internally inconsistent. Each
check exists because its failure mode actually happened:

  2026-07-31  ledger missing the v1.1 amendment entry (found internally)
  2026-07-31  published hashes truncated to 12/16 hex (found internally)
  2026-08-01  frozen v1 sources absent -> version unverifiable (found by an
              independent model audit; see the ledger)
  2026-08-01  re-running the build with a stale --version re-froze v1 from
              v1.1 bytes (caught pre-push, in-session)

The premise of the whole instrument is that a model can check us. This script
is us checking ourselves the same way, mechanically, on every publish.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
errors = []


def err(msg):
    errors.append(msg)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


versions = json.loads((REPO / "commitment/history/versions.json").read_text())

# 1. Every listed version has frozen sources, and they hash to the manifest.
for v in versions:
    for part in ("commitment", "details"):
        p = REPO / f"commitment/history/{v['version']}/{part}.md"
        if not p.exists():
            err(f"{v['version']}: frozen source missing: {p.relative_to(REPO)}")
        elif sha(p) != v["sha256"][part]:
            err(f"{v['version']}/{part}.md hashes {sha(p)[:12]}…, manifest says "
                f"{v['sha256'][part][:12]}… — a frozen version has been altered")

# 2. Live sources match the NEWEST version exactly (stale live text or an
#    unfrozen new issuance both fail here).
newest = versions[-1]
for part in ("commitment", "details"):
    live = sha(REPO / f"commitment/{part}.md")
    if live != newest["sha256"][part]:
        err(f"live {part}.md ({live[:12]}…) does not match newest version "
            f"{newest['version']} ({newest['sha256'][part][:12]}…) — "
            f"either freeze a new version or the live text drifted")

# 3. The ledger records an amendment entry for every issued version.
ledger = (REPO / "commitment/ledger/index.html").read_text()
for v in versions:
    if v["version"] not in ledger:
        err(f"ledger has no entry mentioning {v['version']} — the ledger "
            f"promises to record every amendment")

# 4. Rendered pages carry every full 64-hex hash (truncated display regression).
history_html = (REPO / "commitment/history/index.html").read_text()
for v in versions:
    for part in ("commitment", "details"):
        if v["sha256"][part] not in history_html:
            err(f"history page lacks the full {v['version']} {part} hash — "
                f"a truncated display can only be verified to 48 bits")
commitment_html = (REPO / "commitment/index.html").read_text()
if newest["sha256"]["commitment"] not in commitment_html:
    err("commitment page lacks its own full source hash")

# 5. Ledger discipline: entries are append-only tables; every entry table
#    needs date/type/version fields present.
entry_count = len(re.findall(r"<th>Entry \d+</th>", ledger))
for field in ("date", "type", "commitment version"):
    n = len(re.findall(f"<code>{field}</code>", ledger))
    if n < entry_count:
        err(f"ledger: {entry_count} entries but only {n} '{field}' fields")

if errors:
    print("check-record: RECORD INCONSISTENT — do not publish:", file=sys.stderr)
    for e in errors:
        print(f"  ✗ {e}", file=sys.stderr)
    sys.exit(1)
print(f"check-record: OK — {len(versions)} versions, {entry_count} ledger entries, "
      f"all frozen sources hash-verified, full hashes rendered")
