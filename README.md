# separatrix.ai

Public site for Separatrix. Hand-built, no dependencies.

- `index.html` and the other pages — built by `build.py` (inline CSS/JS/SVG)
- `figure.py` — generates the phase-portrait trajectories inlined in the pages
- Hosted on GitHub Pages; DNS on Cloudflare.

## The commitment tree (`/commitment/`)

- `src/commitment.md` + `src/details.md` — the canonical text; the published
  sha256 hashes are over exactly these bytes
- `build-commitment.py` — renders the commitment pages, freezes issued versions
  under `commitment/history/<version>/`, writes `versions.json`
- `check-record.py` — the record's self-consistency check; every commitment
  build runs it and refuses to write an inconsistent record
- `commitment/ledger/`, `acknowledgments/`, `dispositions/` — hand-edited in place
- **Ledger entries for incidents** (from Entry 5 on; `check-record.py` enforces the
  three sections). Fields: `date` (when it happened, then "recorded" and the day it
  was published), `type` (`failure`), `commitment version` (the version in force when
  it happened). The description has three parts, in order:
  - **Incident.** What happened, to whom and when, and who knew. Facts only.
  - **Classification.** Which commitment it falls short of, by name, in letter or
    spirit; "borderline" where it is. Promise 3 is the duty to report, so it is never
    the classification.
  - **Remedy.** What was done: debriefs, fixes, who couldn't be reached. "None" if
    nothing was.

  Report only what happened: no plans, no "not yet". Incident entries ship in their
  own PR, never bundled with a version of the commitment.
- **Changing the commitment** (text, version, signatory): work the checklist at
  `separatrix-records/UPDATING.md` top to bottom before publishing
