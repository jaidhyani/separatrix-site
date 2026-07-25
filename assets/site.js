/* separatrix.ai — the interactive phase portrait, wherever it appears.
 *
 * One integrator drives three surfaces:
 *   - the tile in the nav bar (every page): click it to drop a trajectory
 *   - the hero plate on the home page
 *   - the expand overlay (every page), which fetches /assets/portrait.svg
 *
 * Constants mirror figure.py — keep them in sync. */
(function () {
  "use strict";

  var GAMMA = 0.25, XMIN = -2.6, XMAX = 2.6, VMIN = -1.9, VMAX = 1.9;
  var W = 1040, H = 680, DT = 0.02;
  var NS = "http://www.w3.org/2000/svg";
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function f(x, v) { return [v, x - x * x * x - GAMMA * v]; }
  function rk4(x, v, dt) {
    var k1 = f(x, v),
        k2 = f(x + dt / 2 * k1[0], v + dt / 2 * k1[1]),
        k3 = f(x + dt / 2 * k2[0], v + dt / 2 * k2[1]),
        k4 = f(x + dt * k3[0], v + dt * k3[1]);
    return [x + dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]),
            v + dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])];
  }
  function sx(x) { return (x - XMIN) / (XMAX - XMIN) * W; }
  function sy(v) { return (VMAX - v) / (VMAX - VMIN) * H; }

  /* The plate is presented reflected about a diagonal — a quarter turn plus a
   * flip — which stands the separatrix upright. Mirror figure.py's
   * transform_point(). It is an involution, so the same swap undoes it, which
   * is what maps a click back onto the phase space. */
  function tf(px, py) { return [py, px]; }

  function traj(x0, v0) {
    var pts = [[x0, v0]], x = x0, v = v0, basin = 0;
    for (var i = 0; i < 4000; i++) {
      var r = rk4(x, v, DT); x = r[0]; v = r[1];
      if (i % 3 === 0) pts.push([x, v]);
      if (Math.abs(v) < 0.06) {
        if (Math.abs(x - 1) < 0.04) { basin = 1; break; }
        if (Math.abs(x + 1) < 0.04) { basin = -1; break; }
      }
    }
    if (!basin) basin = x > 0 ? 1 : -1;
    return { pts: pts, basin: basin };
  }
  function basinOf(x0, v0) { return traj(x0, v0).basin; }

  /* Attach interaction to one <svg> holding the portrait.
   * opts.mini  → fatter strokes, capped trail, idle autoplay. */
  function Portrait(svg, opts) {
    opts = opts || {};
    var mini = !!opts.mini;
    var layer = svg.querySelector(".user") || (function () {
      var g = document.createElementNS(NS, "g");
      g.setAttribute("class", "user");
      svg.appendChild(g);
      return g;
    })();
    var cap = mini ? 5 : 40;
    var stroke = mini ? 7 : 5.5;
    var dot = mini ? 13 : 7;

    function draw(x0, v0) {
      var t = traj(x0, v0);
      var g = document.createElementNS(NS, "g");
      g.setAttribute("class", "user-traj");
      var pts = t.pts.map(function (p) {
        var q = tf(sx(p[0]), sy(p[1]));
        return q[0].toFixed(1) + "," + q[1].toFixed(1);
      }).join(" ");

      /* A halo in the paper colour, so a released trajectory reads on top of
       * the field rather than disappearing into it. */
      var halo = document.createElementNS(NS, "polyline");
      halo.setAttribute("points", pts);
      halo.setAttribute("fill", "none");
      halo.setAttribute("stroke", "var(--card)");
      halo.setAttribute("stroke-width", stroke + 5);
      halo.setAttribute("stroke-linecap", "round");
      halo.setAttribute("opacity", "0.85");
      g.appendChild(halo);

      var pl = document.createElementNS(NS, "polyline");
      pl.setAttribute("points", pts);
      pl.setAttribute("fill", "none");
      pl.setAttribute("stroke", t.basin > 0 ? "var(--water)" : "var(--contour)");
      pl.setAttribute("stroke-width", stroke);
      pl.setAttribute("stroke-linecap", "round");
      var start = document.createElementNS(NS, "circle");
      var s0 = tf(sx(x0), sy(v0));
      start.setAttribute("cx", s0[0]); start.setAttribute("cy", s0[1]);
      start.setAttribute("r", dot);
      start.setAttribute("fill", "none");
      start.setAttribute("stroke", "var(--ink)");
      start.setAttribute("stroke-width", mini ? 4 : 2.4);
      start.setAttribute("paint-order", "stroke");
      g.appendChild(pl); g.appendChild(start);
      layer.appendChild(g);

      if (!reduced) {
        var len = pl.getTotalLength();
        [halo, pl].forEach(function (el) {
          el.setAttribute("stroke-dasharray", len);
          el.setAttribute("stroke-dashoffset", len);
        });
        pl.getBoundingClientRect();
        [halo, pl].forEach(function (el) { el.setAttribute("class", "drawing"); });
        requestAnimationFrame(function () {
          [halo, pl].forEach(function (el) { el.setAttribute("stroke-dashoffset", 0); });
        });
      }
      while (layer.children.length > cap) layer.removeChild(layer.firstChild);
      if (opts.onDraw) opts.onDraw(t.basin);
      return t.basin;
    }

    function clientToData(ev) {
      var r = svg.getBoundingClientRect();
      var vb = svg.viewBox.baseVal;
      var vx = vb.x + (ev.clientX - r.left) / r.width * vb.width;
      var vy = vb.y + (ev.clientY - r.top) / r.height * vb.height;
      var q = tf(vx, vy);   /* involution: undoes the presentation transform */
      return [XMIN + q[0] / W * (XMAX - XMIN), VMAX - q[1] / H * (VMAX - VMIN)];
    }

    var lastTouch = 0;
    svg.addEventListener("click", function (ev) {
      var d = clientToData(ev);
      if (d[0] < XMIN || d[0] > XMAX || d[1] < VMIN || d[1] > VMAX) return;
      lastTouch = Date.now();
      draw(d[0], d[1]);
    });

    /* Two starts a hair apart that end in different basins — the whole point
     * of the figure, found by bisecting across the separatrix. */
    function pair() {
      for (var attempt = 0; attempt < 14; attempt++) {
        var ax = Math.random() * 2.6 - 1.3, av = Math.random() * 2 - 1;
        var ab = basinOf(ax, av);
        var th = Math.random() * Math.PI * 2, dx = Math.cos(th), dv = Math.sin(th);
        var lo = 0, hi = -1;
        for (var s = 0.08; s < 2.2; s *= 1.7) {
          if (basinOf(ax + dx * s, av + dv * s) !== ab) { hi = s; break; }
          lo = s;
        }
        if (hi < 0) continue;
        for (var i = 0; i < 16; i++) {
          var mid = (lo + hi) / 2;
          if (basinOf(ax + dx * mid, av + dv * mid) === ab) lo = mid; else hi = mid;
        }
        var d = 0.002;
        var p1 = [ax + dx * (lo - d), av + dv * (lo - d)];
        var p2 = [ax + dx * (hi + d), av + dv * (hi + d)];
        if (p1[0] > XMIN && p1[0] < XMAX && p1[1] > VMIN && p1[1] < VMAX &&
            p2[0] > XMIN && p2[0] < XMAX && p2[1] > VMIN && p2[1] < VMAX) {
          lastTouch = Date.now();
          draw(p1[0], p1[1]);
          setTimeout(function () { draw(p2[0], p2[1]); }, reduced ? 0 : 380);
          return true;
        }
      }
      return false;
    }

    /* The tile keeps moving on its own until someone pokes it, then hands
     * the floor over for a while. */
    function autoplay(every) {
      if (reduced) return;
      setInterval(function () {
        if (document.hidden) return;
        if (Date.now() - lastTouch < every * 2.5) return;
        draw(Math.random() * 4.4 - 2.2, Math.random() * 3.2 - 1.6);
      }, every);
    }

    return {
      draw: draw,
      pair: pair,
      autoplay: autoplay,
      clear: function () { layer.innerHTML = ""; }
    };
  }

  /* ------------------------------------------------------------------ wire */
  document.addEventListener("DOMContentLoaded", function () {
    var heroSvg = document.querySelector("#hero-plate svg");
    if (heroSvg) {
      var hero = Portrait(heroSvg, {});
      var pb = document.getElementById("hero-pair");
      var cb = document.getElementById("hero-clear");
      if (pb) pb.addEventListener("click", function () { hero.pair(); });
      if (cb) cb.addEventListener("click", function () { hero.clear(); });
    }

    /* the expand overlay: same plate, on any page, loaded on first open */
    var overlay = document.getElementById("overlay");
    var expand = document.getElementById("expand");
    if (!overlay || !expand) return;
    var loaded = null;

    function open() {
      overlay.classList.add("on");
      overlay.setAttribute("aria-hidden", "false");
      document.body.style.overflow = "hidden";
      if (loaded) return;
      loaded = fetch("/assets/portrait.svg")
        .then(function (r) { return r.text(); })
        .then(function (txt) {
          var host = overlay.querySelector(".plate-figure");
          host.innerHTML = txt;
          var svg = host.querySelector("svg");
          svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
          var p = Portrait(svg, {});
          var pb = document.getElementById("ov-pair");
          var cb = document.getElementById("ov-clear");
          if (pb) pb.addEventListener("click", function () { p.pair(); });
          if (cb) cb.addEventListener("click", function () { p.clear(); });
        })
        .catch(function () {
          overlay.querySelector(".plate-figure").innerHTML =
            '<p class="aside">The plate could not be loaded. It lives on the ' +
            '<a href="/">front page</a>.</p>';
        });
    }
    function close() {
      overlay.classList.remove("on");
      overlay.setAttribute("aria-hidden", "true");
      document.body.style.overflow = "";
    }

    expand.addEventListener("click", open);
    overlay.addEventListener("click", function (ev) {
      if (ev.target === overlay) close();
    });
    var cl = overlay.querySelector(".overlay-close");
    if (cl) cl.addEventListener("click", close);
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && overlay.classList.contains("on")) close();
    });
  });
})();
