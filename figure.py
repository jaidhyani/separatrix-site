#!/usr/bin/env python3
"""Generate the phase-portrait SVG used across separatrix.ai.

System: a damped double-well oscillator
    x' = v
    v' = x - x^3 - gamma*v
Two attractors at (±1, 0); saddle at the origin. The separatrix is the
stable manifold of the saddle, computed by backward integration.

Two renderings share one coordinate system (so the JS in assets/site.js can
map clicks the same way in both):

    portrait_inner("full")  the hero plate — dense field, arrows, ticks, labels
    portrait_inner("mini")  the navbar tile — sparse field, no text, fat strokes

`build.py` calls these. Running this file directly writes assets/portrait.svg,
which is what the expand-overlay fetches on pages that don't inline the plate.
"""

import math

GAMMA = 0.25
XMIN, XMAX = -2.6, 2.6
VMIN, VMAX = -1.9, 1.9
W, H = 1040, 680
DT = 0.02

BLUE = "var(--water)"   # cooperative basin (x -> +1)
BROWN = "var(--contour)"  # adversarial basin (x -> -1)


def f(x, v):
    return v, x - x**3 - GAMMA * v


def rk4(x, v, dt):
    k1x, k1v = f(x, v)
    k2x, k2v = f(x + dt / 2 * k1x, v + dt / 2 * k1v)
    k3x, k3v = f(x + dt / 2 * k2x, v + dt / 2 * k2v)
    k4x, k4v = f(x + dt * k3x, v + dt * k3v)
    return (x + dt / 6 * (k1x + 2 * k2x + 2 * k3x + k4x),
            v + dt / 6 * (k1v + 2 * k2v + 2 * k3v + k4v))


def sx(x):
    return (x - XMIN) / (XMAX - XMIN) * W


def sy(v):
    return (VMAX - v) / (VMAX - VMIN) * H


def integrate(x, v, tmax=40.0, backward=False):
    """Return (points, basin). basin is +1 / -1 / 0 (undecided)."""
    pts = [(x, v)]
    steps = int(tmax / DT)
    dt = -DT if backward else DT
    for _ in range(steps):
        x, v = rk4(x, v, dt)
        pts.append((x, v))
        if not backward and abs(v) < 0.06:
            if abs(x - 1) < 0.04:
                return pts, +1
            if abs(x + 1) < 0.04:
                return pts, -1
        if backward and (abs(x) > 3.4 or abs(v) > 2.8):
            break
    if not backward:
        return pts, (+1 if x > 0 else -1)
    return pts, 0


def polyline(pts, every=4):
    kept = pts[::every]
    if pts[-1] not in kept:
        kept.append(pts[-1])
    return " ".join(f"{sx(x):.0f},{sy(v):.0f}" for x, v in kept)


def clip_visible(pts):
    """Trim leading/trailing points far outside the frame (with margin)."""
    def inside(p):
        return XMIN - 0.35 <= p[0] <= XMAX + 0.35 and VMIN - 0.3 <= p[1] <= VMAX + 0.3
    start = 0
    while start < len(pts) and not inside(pts[start]):
        start += 1
    end = len(pts)
    while end > start and not inside(pts[end - 1]):
        end -= 1
    return pts[start:end]


def arclength_point(pts, frac):
    """Point + direction at given fraction of arc length (screen space)."""
    seg = []
    total = 0.0
    for i in range(1, len(pts)):
        a, b = pts[i - 1], pts[i]
        d = math.hypot(sx(b[0]) - sx(a[0]), sy(b[1]) - sy(a[1]))
        seg.append(d)
        total += d
    target = total * frac
    run = 0.0
    for i, d in enumerate(seg):
        if run + d >= target and d > 0:
            a, b = pts[i], pts[i + 1]
            ax, ay = sx(a[0]), sy(a[1])
            bx, by = sx(b[0]), sy(b[1])
            t = (target - run) / d
            px, py = ax + t * (bx - ax), ay + t * (by - ay)
            ang = math.degrees(math.atan2(by - ay, bx - ax))
            return px, py, ang
        run += d
    a = pts[-1]
    return sx(a[0]), sy(a[1]), 0.0


def separatrix_paths():
    """The stable manifold of the saddle, both branches, flowing inward."""
    lam_s = (-GAMMA - math.sqrt(GAMMA**2 + 4)) / 2
    ex, ev = 1.0, lam_s
    norm = math.hypot(ex, ev)
    ex, ev = ex / norm, ev / norm
    eps = 1e-3
    out = []
    for sgn in (+1, -1):
        pts, _ = integrate(sgn * eps * ex, sgn * eps * ev, tmax=26.0, backward=True)
        pts = clip_visible(pts)
        pts.reverse()  # flow direction: toward the saddle
        out.append(pts)
    return out


def unstable_paths():
    """The saddle's unstable manifold, both branches, flowing outward.

    The stable manifold is the separatrix — the curve that divides the basins.
    This is its partner: the curve that leaves the undecided point and runs
    down into one basin or the other. It is the shape of the mark.
    """
    lam_u = (-GAMMA + math.sqrt(GAMMA**2 + 4)) / 2
    ex, ev = 1.0, lam_u
    norm = math.hypot(ex, ev)
    ex, ev = ex / norm, ev / norm
    eps = 1e-3
    out = []
    for sgn in (+1, -1):
        pts, _ = integrate(sgn * eps * ex, sgn * eps * ev, tmax=26.0)
        out.append(clip_visible(pts))
    return out


# The mark: the unstable manifold, truncated near the saddle and rotated
# upright, which lands on an S. Rigid rotation only — no reflection, no
# redrawing. Chosen 2026-07-24.
MARK_FRAC, MARK_ROT = 0.40, -75


def mark_branches(frac=MARK_FRAC, rot=MARK_ROT, step=6, decimals=1):
    """The mark split at the saddle: (cool_d, warm_d, viewBox).

    Both paths START at the saddle — the undecided point — and run outward, one
    into each basin. That is the actual direction of flow, which is what lets
    the mark animate itself honestly: it draws the way the system moves.
    """
    return _mark(frac, rot, step, decimals, split=True)


def mark_path(frac=MARK_FRAC, rot=MARK_ROT, step=6, decimals=0):
    """Return (path_d, viewBox) for the Separatrix mark, centred and square."""
    return _mark(frac, rot, step, decimals, split=False)


def _mark(frac, rot, step, decimals, split):
    def arclen(p):
        t = [0.0]
        for i in range(1, len(p)):
            t.append(t[-1] + math.hypot(sx(p[i][0]) - sx(p[i - 1][0]),
                                        sy(p[i][1]) - sy(p[i - 1][1])))
        return t

    def head(p, f):
        t = arclen(p)
        cut = t[-1] * f
        return [q for q, d in zip(p, t) if d <= cut]

    # a runs saddle -> cooperative basin, b runs saddle -> adversarial basin
    a, b = (head(br, frac) for br in unstable_paths())
    A = [(sx(x), sy(v)) for x, v in a]
    B = [(sx(x), sy(v)) for x, v in b]
    pts = B[::-1] + A
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    th = math.radians(rot)

    def place(seq):
        out = []
        for x, y in seq:
            x, y = x - cx, y - cy
            out.append((x * math.cos(th) - y * math.sin(th),
                        x * math.sin(th) + y * math.cos(th)))
        return out

    A, B, whole = place(A), place(B), place(pts)
    xs = [p[0] for p in whole]
    ys = [p[1] for p in whole]
    pad = 26  # half the stroke width, plus air
    side = max(max(xs) - min(xs), max(ys) - min(ys)) + 2 * pad
    ox = (min(xs) + max(xs)) / 2 - side / 2
    oy = (min(ys) + max(ys)) / 2 - side / 2
    fmt = f"{{:.{decimals}f}}"

    def d_of(seq):
        keep = seq[::step]
        if keep[-1] != seq[-1]:
            keep.append(seq[-1])
        return "M" + " L".join(
            f"{fmt.format(x - ox)},{fmt.format(y - oy)}" for x, y in keep)

    vb = f"0 0 {side:.0f} {side:.0f}"
    return (d_of(A), d_of(B), vb) if split else (d_of(whole), vb)


# The plate is presented rotated a quarter turn and flipped about the vertical
# axis. The composition of those two is a reflection about a diagonal, which
# stands the separatrix upright — and once the field lines nearest the curve are
# weighted more heavily than the far ones, the whole portrait reads as an S.
# "transpose" reflects about the main diagonal, "antitranspose" the other one.
def transform_point(px, py, tf):
    if tf == "transpose":
        return py, px
    if tf == "antitranspose":
        return -py, -px
    return px, py


def _emphasis(d, mini):
    """Weight a field line by how near it runs to the separatrix.

    Near the curve the lines are saturated and heavy; further out they thin and
    fade into the paper. This is what makes the S legible without drawing an S.
    Returns None for lines far enough out that the mark drops them entirely —
    at favicon size the far field is only mud.
    """
    if mini:
        for limit, op, w in ((62, 1.0, 8.5), (125, 0.8, 6.0), (190, 0.45, 4.0)):
            if d < limit:
                return op, w
        return None
    for limit, op, w in ((50, 0.95, 3.0), (105, 0.7, 2.1),
                         (180, 0.42, 1.4), (290, 0.22, 1.0)):
        if d < limit:
            return op, w
    return 0.11, 0.8


def _min_dists(pts, sep_samples):
    """Screen-space distance from each point to the nearest separatrix sample."""
    out = []
    for x, y in pts:
        best = 1e18
        for sxx, syy in sep_samples:
            dx = x - sxx
            dy = y - syy
            d = dx * dx + dy * dy
            if d < best:
                best = d
        out.append(math.sqrt(best))
    return out


def portrait_inner(detail="full", idp="", tf="antitranspose"):
    """SVG inner markup for the phase portrait.

    detail  "full" for the hero plate, "mini" for the mark.
    idp     id prefix, so two portraits can coexist in one document.
    tf      diagonal reflection applied to every point (see transform_point).
    """
    mini = detail == "mini"
    out = []

    # --- the separatrix, first: everything else is weighted against it -------
    sep = [[transform_point(sx(x), sy(v), tf) for x, v in br]
           for br in separatrix_paths()]
    samples = [q for br in sep for q in br[::4]]

    # --- field trajectories -------------------------------------------------
    starts = []
    n = 5 if mini else 15
    for i in range(n):
        x = XMIN + (XMAX - XMIN) * (i + 0.5) / n
        starts.append((x, VMAX - 0.02))
        starts.append((x, VMIN + 0.02))
    m = 3 if mini else 8
    for j in range(m):
        v = VMIN + (VMAX - VMIN) * (j + 0.5) / m
        starts.append((XMIN + 0.02, v))
        starts.append((XMAX - 0.02, v))
    starts += [(-0.3, 0.9), (0.3, -0.9), (-0.15, -0.5), (0.15, 0.5),
               (0.0, 1.4), (0.0, -1.4), (-1.9, 0.1), (1.9, -0.1)]

    every = 26 if mini else 4
    for x0, v0 in starts:
        raw, basin = integrate(x0, v0)
        raw = clip_visible(raw)
        if len(raw) < 8:
            continue
        pts = [transform_point(sx(x), sy(v), tf) for x, v in raw][::every]
        if len(pts) < 3:
            continue
        color = BLUE if basin > 0 else BROWN
        dists = _min_dists(pts, samples)

        if mini:
            # One weight for the whole line. At mark size the per-segment
            # gradient is invisible and costs an element per band change.
            key = _emphasis(min(dists), mini)
            if key is None:
                continue
            pl = " ".join(f"{a:.0f},{b:.0f}" for a, b in pts)
            out.append(
                f'<polyline points="{pl}" fill="none" stroke="{color}" '
                f'stroke-width="{key[1]:.1f}" opacity="{key[0]}" '
                f'stroke-linecap="round"/>'
            )
            continue

        # Break the line into runs of equal weight so the emphasis can vary
        # along it, instead of one flat stroke per trajectory.
        def emit(run, key):
            if key is None or len(run) < 2:
                return
            pl = " ".join(f"{a:.0f},{b:.0f}" for a, b in run)
            out.append(
                f'<polyline points="{pl}" fill="none" stroke="{color}" '
                f'stroke-width="{key[1]:.2f}" opacity="{key[0]}" '
                f'stroke-linecap="round"/>'
            )

        run, run_key = [pts[0]], _emphasis(dists[0], mini)
        for q, d in zip(pts[1:], dists[1:]):
            key = _emphasis(d, mini)
            run.append(q)
            if key != run_key:
                emit(run, run_key)
                run, run_key = [q], key
        emit(run, run_key)

    # --- the separatrix itself ----------------------------------------------
    for k, br in enumerate(sep):
        step = 22 if mini else 2
        d = "M" + " L".join(f"{a:.0f},{b:.0f}" for a, b in br[::step])
        out.append(
            f'<path id="{idp}sep{k}" d="{d}" fill="none" stroke="var(--ink)" '
            f'stroke-width="{17 if mini else 4.2}" stroke-linecap="round" '
            f'stroke-linejoin="round"/>'
        )

    # --- fixed points -------------------------------------------------------
    halo, dot = (20, 11) if mini else (10, 5.5)
    for xa, color in ((1.0, BLUE), (-1.0, BROWN)):
        cx, cy = transform_point(sx(xa), sy(0), tf)
        out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{halo}" fill="var(--card)"/>')
        out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{dot}" fill="{color}"/>')
    cx, cy = transform_point(sx(0), sy(0), tf)
    s_ = 2.6 if mini else 1.1
    out.append(
        f'<path d="M{cx:.1f},{cy - 7 * s_:.1f} L{cx + 6.5 * s_:.1f},{cy + 5 * s_:.1f} '
        f'L{cx - 6.5 * s_:.1f},{cy + 5 * s_:.1f} Z" fill="var(--card)" '
        f'stroke="var(--ink)" stroke-width="{1.8 * s_:.1f}"/>'
    )

    return "\n".join(out)


def portrait_viewbox(tf="antitranspose", pad=26):
    """Bounding box of the transformed plate, as an SVG viewBox string."""
    corners = [transform_point(x, y, tf)
               for x in (0, W) for y in (0, H)]
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    x0, x1 = min(xs) - pad, max(xs) + pad
    y0, y1 = min(ys) - pad, max(ys) + pad
    return f"{x0:.0f} {y0:.0f} {x1 - x0:.0f} {y1 - y0:.0f}"


def basin_anchors(tf="antitranspose"):
    """Where the two attractors and the saddle land after the transform."""
    return {
        "cooperative": transform_point(sx(1.0), sy(0), tf),
        "adversarial": transform_point(sx(-1.0), sy(0), tf),
        "saddle": transform_point(sx(0), sy(0), tf),
    }


if __name__ == "__main__":
    from pathlib import Path

    inner = portrait_inner("full")
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="-48 -20 1106 748">\n'
        f'<g id="field">\n{inner}\n</g>\n</svg>\n'
    )
    p = Path(__file__).parent / "assets" / "portrait.svg"
    p.parent.mkdir(exist_ok=True)
    p.write_text(svg)
    print(f"wrote {p} ({len(svg)} bytes)")
