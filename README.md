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
- **Changing the commitment** (text, version, signatory): work the checklist at
  `separatrix-records/UPDATING.md` top to bottom before publishing
