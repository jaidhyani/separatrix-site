#!/usr/bin/env python3
"""Generate the phase-portrait SVG for separatrix.ai.

System: a damped double-well oscillator
    x' = v
    v' = x - x^3 - gamma*v
Two attractors at (±1, 0); saddle at the origin. The separatrix is the
stable manifold of the saddle, computed by backward integration.

Reads index.template.html, replaces <!--PORTRAIT--> with the generated SVG
inner markup, writes index.html.
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


def main():
    out = []

    # --- field trajectories -------------------------------------------------
    starts = []
    # border inflow
    n = 13
    for i in range(n):
        x = XMIN + (XMAX - XMIN) * (i + 0.5) / n
        starts.append((x, VMAX - 0.02))
        starts.append((x, VMIN + 0.02))
    m = 7
    for j in range(m):
        v = VMIN + (VMAX - VMIN) * (j + 0.5) / m
        starts.append((XMIN + 0.02, v))
        starts.append((XMAX - 0.02, v))
    # a few interior seeds near the action
    starts += [(-0.3, 0.9), (0.3, -0.9), (-0.15, -0.5), (0.15, 0.5),
               (0.0, 1.4), (0.0, -1.4), (-1.9, 0.1), (1.9, -0.1)]

    arrows = []
    for i, (x0, v0) in enumerate(starts):
        pts, basin = integrate(x0, v0)
        pts = clip_visible(pts)
        if len(pts) < 8:
            continue
        color = BLUE if basin > 0 else BROWN
        out.append(
            f'<polyline points="{polyline(pts)}" fill="none" '
            f'stroke="{color}" stroke-width="1.1" opacity="0.42"/>'
        )
        if i % 5 == 2:
            arrows.append((pts, color))

    for pts, color in arrows:
        px, py, ang = arclength_point(pts, 0.42)
        out.append(
            f'<path d="M-6,-3.4 L1.5,0 L-6,3.4 Z" fill="{color}" opacity="0.75" '
            f'transform="translate({px:.1f},{py:.1f}) rotate({ang:.1f})"/>'
        )

    # --- separatrix: stable manifold of the saddle, integrated backward ----
    lam_s = (-GAMMA - math.sqrt(GAMMA**2 + 4)) / 2
    ex, ev = 1.0, lam_s
    norm = math.hypot(ex, ev)
    ex, ev = ex / norm, ev / norm
    eps = 1e-3
    sep_paths = []
    for sgn in (+1, -1):
        pts, _ = integrate(sgn * eps * ex, sgn * eps * ev, tmax=26.0, backward=True)
        pts = clip_visible(pts)
        pts.reverse()  # flow direction: toward the saddle
        sep_paths.append(pts)

    for k, pts in enumerate(sep_paths):
        d = "M" + " L".join(f"{sx(x):.1f},{sy(v):.1f}" for x, v in pts[::2])
        pid = f"sep{k}"
        out.append(
            f'<path id="{pid}" d="{d}" fill="none" stroke="var(--ink)" '
            f'stroke-width="2.4" stroke-linecap="round"/>'
        )
        px, py, ang = arclength_point(pts, 0.6)
        out.append(
            f'<path d="M-7,-4 L2,0 L-7,4 Z" fill="var(--ink)" '
            f'transform="translate({px:.1f},{py:.1f}) rotate({ang:.1f})"/>'
        )

    # label the curve along its own path, cartography-style
    out.append(
        '<text class="fig-feature" dy="-7">'
        '<textPath href="#sep0" startOffset="46%">S E P A R A T R I X</textPath></text>'
    )

    # --- fixed points -------------------------------------------------------
    for xa, color, anchor, dx in ((1.0, BLUE, "start", 14), (-1.0, BROWN, "end", -14)):
        cx, cy = sx(xa), sy(0)
        out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="9" fill="var(--paper)"/>')
        out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" fill="{color}"/>')
    # saddle: triangulation-station triangle
    cx, cy = sx(0), sy(0)
    out.append(
        f'<path d="M{cx:.1f},{cy - 7:.1f} L{cx + 6.5:.1f},{cy + 5:.1f} '
        f'L{cx - 6.5:.1f},{cy + 5:.1f} Z" fill="var(--paper)" '
        f'stroke="var(--ink)" stroke-width="1.8"/>'
    )

    # --- frame ticks (map neatline style) ------------------------------------
    ticks = []
    for xv in (-2, -1, 0, 1, 2):
        px = sx(xv)
        ticks.append(f'<line x1="{px:.1f}" y1="{H}" x2="{px:.1f}" y2="{H + 8}" class="tick"/>')
        ticks.append(f'<text x="{px:.1f}" y="{H + 22}" class="fig-tick" text-anchor="middle">{xv}</text>')
    for vv in (-1, 0, 1):
        py = sy(vv)
        ticks.append(f'<line x1="-8" y1="{py:.1f}" x2="0" y2="{py:.1f}" class="tick"/>')
        ticks.append(f'<text x="-14" y="{py + 4:.1f}" class="fig-tick" text-anchor="end">{vv}</text>')
    out += ticks

    svg_inner = "\n".join(out)

    with open("index.template.html") as fh:
        tpl = fh.read()
    html = tpl.replace("<!--PORTRAIT-->", svg_inner)
    with open("index.html", "w") as fh:
        fh.write(html)
    print(f"wrote index.html ({len(html)} bytes), portrait {len(svg_inner)} bytes")


if __name__ == "__main__":
    main()
