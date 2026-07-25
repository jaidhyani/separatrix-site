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

# How much of each separatrix branch, measured back from the saddle, forms the S.
# Past about 0.24 the ends curl back past the bowls and it stops reading as a letter.
S_FRAC = 0.20

# The falloff. HALO is how wide a band around the S the field survives in at
# full strength; BLUR is how far it takes to fade; GAMMA > 1 makes that fade
# accelerate, so the field disappears rather than merely dimming.
# (named FALL_GAMMA, not GAMMA — GAMMA is the system's damping coefficient)
HALO, BLUR, FALL_GAMMA = 110, 60, 2.4
HALO_MINI, BLUR_MINI = 130, 70
FIELD_W, FIELD_W_MINI = 2.0, 5.0
FIELD_OP = 0.85

# The S itself is drawn by real trajectories: one released a hair to either
# side of the stable manifold, right where the S begins. Each shadows the
# separatrix in toward the saddle, peels off along the unstable manifold into
# its basin, and is clipped where it leaves the S's neighbourhood. The clip is
# aesthetic, not mathematical — but the lines are honest integrations.
EDGE_EPS = 0.008        # data-space offset of the release points
EDGE_KEEP = 90.0        # screen px: how far from the S the bright part survives
EDGE_W, EDGE_W_MINI = 7.0, 18.0


def _box(tf):
    """Generous user-space bounds for the mask region."""
    corners = [transform_point(x, y, tf) for x in (0, W) for y in (0, H)]
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    pad = 400
    return (f"{min(xs) - pad:.0f}", f"{min(ys) - pad:.0f}",
            f"{max(xs) - min(xs) + 2 * pad:.0f}", f"{max(ys) - min(ys) + 2 * pad:.0f}")


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


def sep_split(frac, tf):
    """Split the separatrix into the part that draws the S and the rest.

    Each branch runs from far away in to the saddle. The stretch nearest the
    saddle is what reads as an S; the far stretch curls away and closes the
    shape, which fights it. So they get drawn very differently.
    """
    def arclen(p):
        t = [0.0]
        for i in range(1, len(p)):
            t.append(t[-1] + math.hypot(sx(p[i][0]) - sx(p[i - 1][0]),
                                        sy(p[i][1]) - sy(p[i - 1][1])))
        return t

    core, rest = [], []
    for br in separatrix_paths():
        t = arclen(br)
        cut = t[-1] * (1 - frac)
        near = [q for q, d in zip(br, t) if d >= cut]
        far = [q for q, d in zip(br, t) if d <= cut]
        core.append([transform_point(sx(x), sy(v), tf) for x, v in near])
        rest.append([transform_point(sx(x), sy(v), tf) for x, v in far])
    return core, rest


def _falloff_defs(idp, core_d, halo, blur, gamma, box):
    """A mask whose brightness decays rapidly with distance from the S.

    The field is only drawn where this mask is bright, so everything that is not
    near the curve is subtracted away rather than merely lightened. Without it
    the field lines wrap right around both wells and close the shape into an 8.
    """
    x0, y0, w, h = box
    strokes = "".join(
        f'<path d="{d}" fill="none" stroke="#fff" stroke-width="{halo}" '
        f'stroke-linecap="round" stroke-linejoin="round"/>' for d in core_d
    )
    return (
        f'<defs>'
        f'<filter id="{idp}fall" x="-40%" y="-40%" width="180%" height="180%" '
        f'color-interpolation-filters="sRGB">'
        f'<feGaussianBlur stdDeviation="{blur}"/>'
        f'<feComponentTransfer><feFuncA type="gamma" exponent="{gamma}" amplitude="1"/>'
        f'</feComponentTransfer></filter>'
        f'<mask id="{idp}near" maskUnits="userSpaceOnUse" '
        f'x="{x0}" y="{y0}" width="{w}" height="{h}">'
        f'<g filter="url(#{idp}fall)">{strokes}</g>'
        f'</mask></defs>'
    )


def _edge_starts(frac):
    """Release points for the S trajectories: ±eps off each stable branch,
    at the arclength where the S begins."""
    out = []
    for br in separatrix_paths():
        # br flows toward the saddle; find where the core (the S) starts
        t = [0.0]
        for i in range(1, len(br)):
            t.append(t[-1] + math.hypot(sx(br[i][0]) - sx(br[i - 1][0]),
                                        sy(br[i][1]) - sy(br[i - 1][1])))
        cut = t[-1] * (1 - frac)
        i = max(1, min(next(j for j, d in enumerate(t) if d >= cut), len(br) - 1))
        (x0, v0), (x1, v1) = br[i - 1], br[i]
        tx, tv = x1 - x0, v1 - v0
        n = math.hypot(tx, tv) or 1.0
        px, pv = -tv / n, tx / n
        for sgn in (+1, -1):
            out.append((x0 + sgn * EDGE_EPS * px, v0 + sgn * EDGE_EPS * pv))
    return out


def edge_trajectories(frac=S_FRAC):
    """(points, basin) for each S trajectory, clipped to the S's neighbourhood.

    Distances are measured in untransformed screen space; the presentation
    transform is a rigid reflection, so they carry over unchanged.
    """
    core, _ = sep_split(frac, "none")
    samples = [q for br in core for q in br[::3]]
    out = []
    for x0, v0 in _edge_starts(frac):
        raw, basin = integrate(x0, v0)
        pts = []
        for x, v in raw:
            a, b = sx(x), sy(v)
            d2 = min((a - p) * (a - p) + (b - q) * (b - q) for p, q in samples)
            if d2 > EDGE_KEEP * EDGE_KEEP:
                break
            pts.append((x, v))
        # End at the closest pass to the saddle: past it the trajectory departs
        # along the unstable manifold, which spikes across the middle of the S.
        if pts:
            k = min(range(len(pts)), key=lambda i: pts[i][0] ** 2 + pts[i][1] ** 2)
            pts = pts[:k + 1]
        if len(pts) > 8:
            out.append((pts, basin))
    return out


def portrait_inner(detail="full", idp="", tf="antitranspose"):
    """SVG inner markup for the phase portrait.

    detail  "full" for the hero plate, "mini" for the mark.
    idp     id prefix, so two portraits can coexist in one document.
    tf      diagonal reflection applied to every point (see transform_point).
    """
    mini = detail == "mini"
    out = []

    # --- the S, first: everything else is weighted against it ---------------
    core, rest = sep_split(S_FRAC, tf)
    core_d = ["M" + " L".join(f"{a:.0f},{b:.0f}" for a, b in br[::2]) for br in core]
    field = []

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

    every = 18 if mini else 4
    for x0, v0 in starts:
        raw, basin = integrate(x0, v0)
        raw = clip_visible(raw)
        if len(raw) < 8:
            continue
        pts = [transform_point(sx(x), sy(v), tf) for x, v in raw][::every]
        if len(pts) < 3:
            continue
        color = BLUE if basin > 0 else BROWN
        pl = " ".join(f"{a:.0f},{b:.0f}" for a, b in pts)
        field.append(
            f'<polyline points="{pl}" fill="none" stroke="{color}" '
            f'stroke-width="{FIELD_W_MINI if mini else FIELD_W}" '
            f'stroke-linecap="round"/>'
        )

    # --- the far reaches of the separatrix: no heavier than the field --------
    for br in rest:
        d = "M" + " L".join(f"{a:.0f},{b:.0f}" for a, b in br[::4])
        field.append(
            f'<path d="{d}" fill="none" stroke="var(--ink)" '
            f'stroke-width="{FIELD_W_MINI if mini else FIELD_W}" '
            f'opacity="0.5" stroke-linecap="round"/>'
        )

    box = _box(tf)
    out.append(_falloff_defs(idp, core_d,
                             HALO_MINI if mini else HALO,
                             BLUR_MINI if mini else BLUR,
                             FALL_GAMMA, box))
    out.append(f'<g mask="url(#{idp}near)" opacity="{FIELD_OP}">'
               + "".join(field) + '</g>')

    # --- the S itself: a bright trajectory riding each side of the curve ----
    ew = EDGE_W_MINI if mini else EDGE_W
    for pts_e, basin in edge_trajectories(S_FRAC):
        step = 4 if mini else 2
        spts = [transform_point(sx(x), sy(v), tf) for x, v in pts_e][::step]
        d = "M" + " L".join(f"{a:.0f},{b:.0f}" for a, b in spts)
        color = "var(--water-bright)" if basin > 0 else "var(--contour-bright)"
        out.append(
            f'<path d="{d}" fill="none" stroke="{color}" '
            f'stroke-width="{ew}" stroke-linecap="round" stroke-linejoin="round"/>'
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


def portrait_viewbox(tf="antitranspose", pad=220):
    """Bounding box of the S plus a margin, as an SVG viewBox string.

    Framed on the curve rather than the whole phase space: the field is masked
    away past the falloff anyway, so bounding the full plate just adds empty
    paper around a letter.
    """
    core, _ = sep_split(S_FRAC, tf)
    xs = [q[0] for br in core for q in br]
    ys = [q[1] for br in core for q in br]
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
