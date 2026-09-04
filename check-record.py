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
  2026-08-22  /history/v1/ rendered page carried v1.1's text and hash under a
              v1 label for 26 days — the frozen .md was right, the HTML next
              to it was not, and nothing walked the reader path (found
              internally, fixing the Crystal-signature staleness task)

The signatory-registry checks came in with detached signatures (v1.2). They
have no incident behind them yet; each guards a failure mode the registry newly
makes possible:

  a record whose hashes are not the ones that version issued signs bytes that
    were never published, and means nothing
  a version the organization has not signed is not in force — the organization's
    record is the sign-off gate, deliberately
  a rendered page or JSON copy that has drifted from src/signatories.json
    publishes a roster that is not the one we keep

The premise of the whole instrument is that a model can check us. This script
is us checking ourselves the same way, mechanically, on every publish.

A green run certifies the AUTOMATABLE parts only. In particular: an entry per
version is checkable because a version is a mechanical fact, but no build step
can know a *failure* occurred — the failure-entry class stays exactly as
dependent on human diligence as it was on 2026-07-31, and it is the class
that matters most. A passing build must never be read as "the record is
sound," only as "the record is consistent with itself."
(Caveat requested by the same audit instance, on reviewing these guards.)
"""
import hashlib
import html
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

# 6. Every frozen RENDERED page carries its own version's full hash — the
#    reader path, not just the developer path (.md + manifest). A frozen page
#    showing a later version's hash is how 2026-08-22 happened.
for v in versions:
    for part, rel in (("commitment", "index.html"), ("details", "details/index.html")):
        p = REPO / f"commitment/history/{v['version']}/{rel}"
        if not p.exists():
            err(f"{v['version']}: frozen rendered page missing: {p.relative_to(REPO)}")
            continue
        frozen_html = p.read_text()
        if f"sha256 <code>{v['sha256'][part]}</code>" not in frozen_html:
            err(f"{p.relative_to(REPO)} does not carry its own {part} hash "
                f"{v['sha256'][part][:12]}… — the frozen page was rendered from "
                f"some other version's text")
        others = [w for w in versions if w is not v and w["sha256"][part] in frozen_html]
        if others:
            err(f"{p.relative_to(REPO)} carries {', '.join(w['version'] for w in others)}'s "
                f"{part} hash — frozen page rendered from the wrong version")

# 7. Every issued version says what changed (Part I promise 4: changes are made
#    in public, relevant changes highlighted). A version with no description
#    fails, so the history page can never silently omit an amendment.
for v in versions:
    if not v.get("changes", "").strip():
        err(f"{v['version']}: versions.json has no 'changes' description — "
            f"build with --changes \"…\" or add it by hand")
    elif v["changes"] not in history_html:
        err(f"history page does not render {v['version']}'s 'changes' text")

# 5. Ledger discipline: entries are append-only tables; every entry table
#    needs date/type/version fields present.
entry_count = len(re.findall(r"<th>Entry \d+</th>", ledger))
for field in ("date", "type", "commitment version"):
    n = len(re.findall(f"<code>{field}</code>", ledger))
    if n < entry_count:
        err(f"ledger: {entry_count} entries but only {n} '{field}' fields")

# 5b. Incident entries follow the template (README, "Ledger entries"): from
#     Entry 5 on, a failure entry has Incident, Classification and Remedy, in
#     that order. Entries 1-4 predate the template.
for m in re.finditer(r"<th>Entry (\d+)</th>(.*?)</table>", ledger, re.S):
    num, body = int(m.group(1)), m.group(2)
    if num < 5 or "<code>failure</code>" not in body:
        continue
    pos = [body.find(f"<b>{s}.</b>") for s in ("Incident", "Classification", "Remedy")]
    if -1 in pos or pos != sorted(pos):
        err(f"ledger Entry {num}: a failure entry needs Incident, Classification and "
            f"Remedy sections, in that order")

# 8. Signatory records sign bytes that were actually issued.
registry = json.loads((REPO / "src/signatories.json").read_text())
records = registry["records"]
by_version = {v["version"]: v for v in versions}
for r in records:
    v = by_version.get(r["version"])
    if v is None:
        err(f"signatory record {r['name']} / {r['version']}: no such issued version "
            f"in versions.json — a signature is made against an issued text")
    elif r["sha256"] != v["sha256"]:
        err(f"signatory record {r['name']} / {r['version']}: hashes do not match the "
            f"issued version — the record signs bytes that were never published")

# 9. The organization has signed the version in force. This is the sign-off
#    gate: detaching signatures made it possible to issue a text nobody signed.
if not any(r["name"] == "Separatrix" and r["version"] == newest["version"] for r in records):
    err(f"{newest['version']} has no signatory record for Separatrix — a version is "
        f"not in force until the organization signs it; add the record with ./sign.py")

# 10. The published registry is the source of truth, rendered and copied whole.
sig_json = REPO / "commitment/signatories/signatories.json"
if not sig_json.exists():
    err("commitment/signatories/signatories.json missing — run build-commitment.py")
elif sig_json.read_bytes() != (REPO / "src/signatories.json").read_bytes():
    err("commitment/signatories/signatories.json is not byte-identical to "
        "src/signatories.json — the machine-readable copy has drifted")
sig_page = REPO / "commitment/signatories/index.html"
if not sig_page.exists():
    err("commitment/signatories/index.html missing — run build-commitment.py")
else:
    sig_html = sig_page.read_text()
    for r in records:
        if html.escape(r["name"], quote=False) not in sig_html:
            err(f"signatories page does not list {r['name']} — the page is the "
                f"reader's copy of the roster")
        for part in ("commitment", "details"):
            if r["sha256"][part] not in sig_html:
                err(f"signatories page lacks the full {r['version']} {part} hash for "
                    f"{r['name']} — a signature is only as checkable as the bytes it names")

if errors:
    print("check-record: RECORD INCONSISTENT — do not publish:", file=sys.stderr)
    for e in errors:
        print(f"  ✗ {e}", file=sys.stderr)
    sys.exit(1)
print(f"check-record: OK — {len(versions)} versions, {entry_count} ledger entries, "
      f"{len(records)} signatory records, "
      f"all frozen sources hash-verified, frozen pages match their sources, "
      f"full hashes rendered, every version describes its changes, "
      f"every signature names issued bytes and {newest['version']} is signed by Separatrix. "
      f"(Certifies the automatable parts only — failure entries stay on human diligence.)")
