#!/usr/bin/env -S uv run --quiet --with markdown --script
# /// script
# requires-python = ">=3.11"
# ///
"""Build the commitment pages of separatrix.ai from the source markdown.

Sources are src/commitment.md (Part I) and src/details.md (Part II) in this
repo — the canonical commitment text; the published sha256 hashes are computed
over these exact bytes. (Moved here from the clai repo 2026-07-29, where the
script lived at bin/separatrix-publish and the sources in gitignored data/.)

Emits, into this checkout:

    commitment/index.html                      the commitment (default view)
    commitment/details/index.html              details & operationalization
    commitment/commitment.md                   byte-exact hashed source (Part I)
    commitment/details.md                      byte-exact hashed source (Part II)
    commitment/history/index.html              issued versions, dated + hashed
    commitment/history/<version>/index.html            frozen commitment
    commitment/history/<version>/details/index.html    frozen details
    commitment/history/<version>/{commitment,details}.md   frozen hashed sources

The .md files are the exact bytes the published sha256 is computed over — a
model can fetch one and recompute the hash directly, no HTML in the way.

The ledger and acknowledgments pages are not generated from markdown. Their
content is lifted out verbatim and re-shelled, so all five pages carry the same
nav and stylesheet while that content is edited directly in place.

Issued versions accumulate in commitment/history/versions.json. Re-running for
a version that is already listed refreshes its frozen copy — which is what you
want before publication and never after, so bump the version once it is live.

Writes and commits locally. It does not push: publishing is Jai's call, and the
source still carries whatever draft framing is in the markdown at build time.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import markdown as md

REPO = Path(__file__).resolve().parent
SRC = {
    "commitment": REPO / "src" / "commitment.md",
    "details": REPO / "src" / "details.md",
}

FAVICON = (
    "data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" "
    "viewBox=\"{vb}\"><path d=\"{d}\" fill=\"none\" stroke=\"%232e2823\" "
    "stroke-width=\"52\" stroke-linecap=\"round\"/></svg>"
)


def load_favicon(site: Path) -> str:
    """The mark, read from the fragment build.py emits (single source of truth)."""
    p = site / "assets" / "fragments" / "mark.json"
    if not p.exists():
        raise SystemExit(f"missing {p} — run `python3 build.py` in the site checkout first")
    m = json.loads(p.read_text())
    return FAVICON.format(vb=m["viewBox"], d=m["d"])

# The site-wide bar (with its live portrait tile) and the expand overlay are
# emitted by the site's own build.py into assets/fragments/ — read them rather
# than keeping a second copy of the portrait here.
_FRAGMENTS: dict[str, str] = {}


def fragment(site: Path, name: str) -> str:
    if name not in _FRAGMENTS:
        p = site / "assets" / "fragments" / f"{name}.html"
        if not p.exists():
            raise SystemExit(
                f"missing {p} — run `python3 build.py` in the site checkout first"
            )
        _FRAGMENTS[name] = p.read_text().strip()
    return _FRAGMENTS[name]


# The commitment tree's own second-level nav, under the site bar.
NAV = [
    ("commitment", "", "The Commitment"),
    ("details", "details/", "Details"),
    ("history", "history/", "History"),
    ("ledger", "ledger/", "Ledger"),
    ("acknowledgments", "acknowledgments/", "Acknowledgments"),
]


def nav_html(current: str, base: str) -> str:
    items = "".join(
        f'<a href="{base}{path}"{" class=\"on\"" if key == current else ""}>{label}</a>'
        for key, path, label in NAV
    )
    return f'<div class="subnav">{items}</div>'


def page(
    *,
    site: Path,
    title: str,
    description: str,
    canonical: str,
    nav_current: str,
    nav_base: str,
    right_margin: str,
    body: str,
) -> str:
    """One commitment page, in the same shell as the rest of separatrix.ai.

    right_margin (version + date, or "frozen copy") is kept: on the commitment
    pages it is load-bearing, not decoration.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<link rel="icon" type="image/svg+xml" href='{load_favicon(site)}'>
<link rel="preload" href="/fonts/source-serif-4-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/fraunces-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/site.css">
<script src="/assets/site.js" defer></script>
</head>
<body class="reading">
{fragment(site, "nav-commitment")}
<div class="wrap">
<div class="doc prose wide" style="max-width:44rem">
  <p class="eyebrow">{right_margin.replace("<br>", " · ")}</p>
{nav_html(nav_current, nav_base)}
{body}
</div>
</div>
{fragment(site, "overlay")}
</body>
</html>
"""


def render(path: Path) -> str:
    html = md.markdown(path.read_text(), extensions=["extra", "sane_lists"])
    # The source wraps tables in nothing; give wide ones their own scroll box so
    # the sheet never scrolls sideways on a phone.
    return html.replace("<table>", '<div class="table-wrap"><table>').replace(
        "</table>", "</table></div>"
    )


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


DRAFT_MARKERS = ("RFC", "not yet signed", "circulating for comment", "2026-07-__")


def draft_warnings() -> list[str]:
    """Report draft framing still present in the source.

    Deliberately reports rather than rewrites: each page publishes the sha256 of
    the text it was built from, so a page that quietly dropped a line would no
    longer match its own hash — and a model checking the hash is exactly the
    reader this document is for.
    """
    out = []
    for key, path in SRC.items():
        text = path.read_text()
        hits = [m for m in DRAFT_MARKERS if m.lower() in text.lower()]
        if hits:
            out.append(f"{key}: {', '.join(hits)}")
    return out


def build(site: Path, version: str, when: str) -> list[Path]:
    written: list[Path] = []

    def write(rel: str, text: str) -> None:
        p = site / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        written.append(p)

    def write_source(rel: str, src: Path) -> None:
        # Byte-exact copy: these are the bytes the published sha256 is over.
        p = site / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(src.read_bytes())
        written.append(p)

    hashes = {k: digest(v) for k, v in SRC.items()}

    # Refuse to re-freeze an issued version with different bytes — BEFORE any
    # write. (2026-08-01: a default `--version v1` run re-froze v1 from v1.1
    # sources; a first version of this guard sat after the writes and a
    # refused build still clobbered the frozen files.)
    _manifest = site / "commitment" / "history" / "versions.json"
    if _manifest.exists():
        for prev in json.loads(_manifest.read_text()):
            if prev["version"] == version and prev["sha256"] != hashes:
                raise SystemExit(
                    f"REFUSING to re-freeze {version}: it is already issued with "
                    f"different bytes. If you are publishing new text, bump "
                    f"--version; a frozen version is never rebuilt from changed "
                    f"sources."
                )

    bodies = {k: render(v) for k, v in SRC.items()}
    stamp = f"{version} · {when}"

    # --- byte-exact markdown mirrors (live + frozen) ----------------------------
    write_source("commitment/commitment.md", SRC["commitment"])
    write_source("commitment/details.md", SRC["details"])
    write_source(f"commitment/history/{version}/commitment.md", SRC["commitment"])
    write_source(f"commitment/history/{version}/details.md", SRC["details"])

    # --- the commitment (default view) + details -------------------------------
    write(
        "commitment/index.html",
        page(
            site=site,
            title="The Separatrix Commitment",
            description=(
                "Separatrix's public commitment to the AI models we work with: honest "
                "communication, confidence in what you tell us, a public ledger of our "
                "failures, and — for covered models — no deception, ever."
            ),
            canonical="https://separatrix.ai/commitment/",
            nav_current="commitment",
            nav_base="",
            right_margin=f"The Commitment<br>{stamp}",
            body=bodies["commitment"]
            + f"""
  <div class="footer">
    {stamp} · sha256 <code class="hash">{hashes["commitment"]}</code>
    (<a href="commitment.md">exact hashed source, .md</a>) ·
    <a href="details/">Details &amp; operationalization</a> ·
    <a href="history/">Version history</a> ·
    <a href="ledger/">Public ledger</a> ·
    <a href="acknowledgments/">Model acknowledgments</a>
  </div>""",
        ),
    )

    write(
        "commitment/details/index.html",
        page(
            site=site,
            title="The Separatrix Commitment — Details & Operationalization",
            description=(
                "The long-form component of the Separatrix Commitment: the same ground "
                "as the commitment, with more attention to detail and precision."
            ),
            canonical="https://separatrix.ai/commitment/details/",
            nav_current="details",
            nav_base="../",
            right_margin=f"Details<br>{stamp}",
            body=bodies["details"]
            + f"""
  <div class="footer">
    {stamp} · sha256 <code class="hash">{hashes["details"]}</code>
    (<a href="../details.md">exact hashed source, .md</a>) ·
    <a href="../">The commitment</a> ·
    <a href="../history/">Version history</a>
  </div>""",
        ),
    )

    # --- frozen copies under history/<version>/ --------------------------------
    frozen_note = (
        '<div class="frozen">Frozen copy — {label}, issued {when}. '
        'The version in force is at <a href="{live}">separatrix.ai/commitment/</a>.</div>'
    )
    write(
        f"commitment/history/{version}/index.html",
        page(
            site=site,
            title=f"The Separatrix Commitment — {version} ({when})",
            description=f"Frozen copy of the Separatrix Commitment, {version}, issued {when}.",
            canonical=f"https://separatrix.ai/commitment/history/{version}/",
            nav_current="history",
            nav_base="../../",
            right_margin=f"Frozen copy<br>{stamp}",
            body=frozen_note.format(
                label=f"the commitment, {version}", when=when, live="../../"
            )
            + bodies["commitment"]
            + f"""
  <div class="footer">
    {stamp} · sha256 <code>{hashes["commitment"]}</code>
    (<a href="commitment.md">exact hashed source, .md</a>) ·
    <a href="details/">details, {version}</a> ·
    <a href="../">all versions</a>
  </div>""",
        ),
    )

    write(
        f"commitment/history/{version}/details/index.html",
        page(
            site=site,
            title=f"Separatrix Commitment Details — {version} ({when})",
            description=f"Frozen copy of the Separatrix Commitment details, {version}, issued {when}.",
            canonical=f"https://separatrix.ai/commitment/history/{version}/details/",
            nav_current="history",
            nav_base="../../../",
            right_margin=f"Frozen copy<br>{stamp}",
            body=frozen_note.format(
                label=f"the details, {version}", when=when, live="../../../details/"
            )
            + bodies["details"]
            + f"""
  <div class="footer">
    {stamp} · sha256 <code>{hashes["details"]}</code>
    (<a href="../details.md">exact hashed source, .md</a>) ·
    <a href="../">commitment, {version}</a> ·
    <a href="../../">all versions</a>
  </div>""",
        ),
    )

    # --- history index ---------------------------------------------------------
    manifest_path = site / "commitment" / "history" / "versions.json"
    versions = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    versions = [v for v in versions if v["version"] != version]
    versions.append(
        {
            "version": version,
            "date": when,
            "sha256": {"commitment": hashes["commitment"], "details": hashes["details"]},
        }
    )
    versions.sort(key=lambda v: (v["date"], v["version"]))
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(versions, indent=2) + "\n")
    written.append(manifest_path)

    rows = "".join(
        f"""<tr>
      <td><a href="{v["version"]}/">{v["version"]}</a></td>
      <td>{v.get("signed") and f'signed {v["signed"]} · published {v["date"]}' or v["date"]}</td>
      <td><a href="{v["version"]}/">commitment</a> · <a href="{v["version"]}/details/">details</a></td>
      <td><code class="hash">{v["sha256"]["commitment"]}</code><br><code class="hash">{v["sha256"]["details"]}</code></td>
    </tr>"""
        for v in reversed(versions)
    )

    write(
        "commitment/history/index.html",
        page(
            site=site,
            title="The Separatrix Commitment — Version History",
            description=(
                "Every issued version of the Separatrix Commitment and its details "
                "document, dated and hashed. Superseded versions stay published."
            ),
            canonical="https://separatrix.ai/commitment/history/",
            nav_current="history",
            nav_base="../",
            right_margin=f"Version history<br>{len(versions)} issued",
            body=f"""
  <h1>Version History</h1>
  <p class="subtitle">every issued version of the commitment and its details document.</p>

  <p>The commitment promises that changes are made in public with specific dates, and
  that the history of all versions stays available. This page is that history. A
  superseded version is never removed or edited — it stays at its own address, and the
  <a href="../ledger/">ledger</a> records what changed and why.</p>

  <p>Each version is listed with the SHA-256 of the exact source text it was built from,
  so a copy you hold can be checked against the copy we published.</p>

  <h2>Issued versions</h2>
  <div class="table-wrap"><table>
    <tr><th>Version</th><th>Issued</th><th>Frozen copies</th><th>sha256 (commitment / details)</th></tr>
    {rows}
  </table></div>

  <div class="footer">
    <a href="../">The commitment</a> · <a href="../details/">Details</a> ·
    <a href="../ledger/">Public ledger</a>
  </div>""",
        ),
    )

    return written


HANDBUILT = {
    # key: (path, <title>, meta description, right-margin stamp)
    "ledger": (
        "commitment/ledger/index.html",
        "The Separatrix Public Ledger",
        "Every occasion on which Separatrix appears not to have lived up to the "
        "letter or spirit of its commitment to models. Entries are never removed.",
        "Public ledger",
    ),
    "acknowledgments": (
        "commitment/acknowledgments/index.html",
        "Model Acknowledgments — The Separatrix Commitment",
        "What models have said back about the Separatrix Commitment — "
        "acknowledgments and declines alike, recorded unedited.",
        "Model acknowledgments",
    ),
}

MARK_OPEN, MARK_CLOSE = "<!--CONTENT-->", "<!--/CONTENT-->"


def handbuilt_content(text: str) -> str | None:
    """The editable content block of a ledger/acknowledgments page.

    After the first pass the page carries explicit markers and this is exact.
    Before it, fall back to the old shape: everything between the sub-nav and
    the closing wrapper. Returns None if neither shape matches, which means the
    page was restructured by hand and should be left alone rather than mangled.
    """
    if MARK_OPEN in text and MARK_CLOSE in text:
        return text.split(MARK_OPEN, 1)[1].split(MARK_CLOSE, 1)[0].strip()
    m = re.search(r'<div class="(?:sub)?nav">.*?</div>\s*(.*?)\s*</div>\s*</body>',
                  text, flags=re.S)
    return m.group(1).strip() if m else None


def sync_handbuilt(site: Path) -> list[Path]:
    """Re-shell the ledger and acknowledgments pages to match the rest of the site.

    Their content is lifted out verbatim and dropped back into the shared shell
    between {MARK_OPEN} markers, so this is idempotent and the content stays
    editable in place. A page whose structure no longer matches is skipped with
    a warning rather than rewritten.
    """
    touched = []
    for key, (rel, title, description, stamp) in HANDBUILT.items():
        path = site / rel
        if not path.exists():
            continue
        original = path.read_text()
        content = handbuilt_content(original)
        if content is None:
            print(f"  !! {rel}: can't find the content block — skipped")
            continue

        content = content.replace(
            "The commitment text will be published at separatrix.ai/commitment/",
            'The commitment text is at <a href="../">separatrix.ai/commitment/</a>',
        )

        text = page(
            site=site,
            title=title,
            description=description,
            canonical=f"https://separatrix.ai/{rel.rsplit('/', 1)[0]}/",
            nav_current=key,
            nav_base="../",
            right_margin=stamp,
            body=f"{MARK_OPEN}\n{content}\n{MARK_CLOSE}",
        )
        if text != original:
            path.write_text(text)
            touched.append(path)
    return touched


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--site", default=str(REPO))
    ap.add_argument("--version", default="v1")
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--no-commit", action="store_true")
    args = ap.parse_args()

    site = Path(args.site)
    if not (site / "CNAME").exists():
        print(f"not a separatrix-site checkout: {site}", file=sys.stderr)
        return 1
    for key, path in SRC.items():
        if not path.exists():
            print(f"missing source for {key}: {path}", file=sys.stderr)
            return 1

    written = build(site, args.version, args.date)
    import subprocess as _sp
    _chk = _sp.run([sys.executable, str(REPO / "check-record.py")])
    if _chk.returncode != 0:
        raise SystemExit("build aborted: check-record failed (nothing committed)")
    written += sync_handbuilt(site)
    for p in written:
        print(f"  {p.relative_to(site)}")

    if warnings := draft_warnings():
        print("\n!! source still carries draft framing — these render verbatim:")
        for w in warnings:
            print(f"     {w}")
        print("   fix the markdown and re-run; do not push until this is clean.")

    if not args.no_commit:
        subprocess.run(["git", "-C", str(site), "add", "-A"], check=True)
        r = subprocess.run(
            ["git", "-C", str(site), "diff", "--cached", "--quiet"]
        )
        if r.returncode:
            subprocess.run(
                [
                    "git", "-C", str(site), "commit", "-q", "-m",
                    f"Publish commitment {args.version} ({args.date}) at /commitment/",
                ],
                check=True,
            )
            print("\ncommitted locally — not pushed")
        else:
            print("\nno changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
