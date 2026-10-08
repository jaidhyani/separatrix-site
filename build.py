#!/usr/bin/env python3
"""Build separatrix.ai.

Emits the four site pages plus assets/portrait.svg (fetched by the expand
overlay on pages that don't inline the plate):

    index.html      the front page - hero, the plate
    approach/       our approach to AI safety
    research/       Reports - primary sources and periodic reports,
                    + per-item pages (path kept at /research/: published
                    URLs under it are cited elsewhere and must not 404)
    who/            people, SNAPS, oversight, Seattle

why_body() and work_body() are retained but unlisted - cut for the MVP
launch (2026-07-25), to return once the content is up to snuff.

The commitment tree under /commitment/ is built separately by this repo's
build-commitment.py from src/commitment.md + src/details.md. Both builders link
/assets/site.css and /assets/site.js, so the nav bar and the look match.

Content lives in this file. It's a small site and one file beats five
partials to keep track of.

    python3 build.py
"""

import json
from pathlib import Path

from figure import (basin_anchors, mark_path,
                    portrait_inner, portrait_viewbox)

ROOT = Path(__file__).resolve().parent

# The mark is the saddle's unstable manifold, truncated and rotated upright -
# the same integration as Fig. 1, no reflection and no redrawing. It happens to
# be an S. See figure.mark_path().
TF = "transpose"   # a quarter turn plus a flip: stands the separatrix upright
PLATE_VB = portrait_viewbox(TF, pad=210)
MARK_VB = portrait_viewbox(TF, pad=120)
_A = basin_anchors(TF)
_ADV_X, _ADV_Y = _A["adversarial"]
_COOP_X, _COOP_Y = _A["cooperative"]
_SAD_X, _SAD_Y = _A["saddle"]

_MARK_D, _MARK_VB = mark_path(step=12)

NAV = [
    ("home", "/", "Separatrix"),
    ("approach", "/approach/", "Approach"),
    ("research", "/research/", "Reports"),
    ("who", "/who/", "Who"),
    ("book", "https://calendar.app.google/qU3H6PGps4CfgamV8", "Book a meeting"),
    ("commitment", "/commitment/", "The Separatrix Commitment"),
    ("manifund", "https://manifund.org/projects/separatrix", "Fund on Manifund"),
]

FAVICON = (
    'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" '
    f'viewBox="{_MARK_VB}"><path d="{_MARK_D}" fill="none" stroke="%232e2823" '
    'stroke-width="52" stroke-linecap="round"/></svg>'
)


def mark_svg() -> str:
    """The mark: the plate itself, cropped and weighted toward the separatrix.

    Same integration and same orientation as Fig. 1 - the lines nearest the
    curve are saturated and heavy, the far field drops away, and what is left
    reads as an S.
    """
    return (f'<svg viewBox="{MARK_VB}" preserveAspectRatio="xMidYMid meet" '
            f'aria-hidden="true" focusable="false">'
            f'{portrait_inner("mini", idp="m", tf=TF)}</svg>')


def nav_html(current: str) -> str:
    """The floating bar. The tile is a live phase portrait you can poke; the
    ⤢ button opens the full plate over whatever page you're on."""
    def item(key, href, label):
        cls = " ".join(filter(None, ["on" if key == current else "",
                                     "cta" if key == "commitment" else "",
                                     "fund" if key == "manifund" else ""]))
        attr = f' class="{cls}"' if cls else ""
        if href.startswith("http"):
            attr += ' target="_blank" rel="noopener"'
        return f'<a href="{href}"{attr}>{label}</a>'

    links = "".join(item(*n) for n in NAV if n[0] != "home")
    return f"""<nav class="nav">
  <div class="nav-inner">
    <a class="tile" id="navtile" href="/"
       title="Separatrix - click to release a trajectory"
       aria-label="Separatrix phase portrait - click to release a trajectory">
{mark_svg()}
    </a>
    <a class="brand" href="/">Separatrix</a>
    <div class="nav-links">{links}</div>
    <button class="expand" id="expand" type="button" title="Open the full plate"
            aria-label="Open the full phase portrait">
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor"
           stroke-width="1.5" stroke-linecap="round"><path d="M5.5 1.5H1.5V5.5M8.5 12.5H12.5V8.5"/>
      <path d="M1.5 1.5L5.5 5.5M12.5 12.5L8.5 8.5"/></svg>
    </button>
  </div>
</nav>"""


OVERLAY = """<div class="overlay" id="overlay" aria-hidden="true" role="dialog"
     aria-label="The phase portrait, full size">
  <button class="overlay-close" type="button" aria-label="Close">&times;</button>
  <figure class="plate">
    <div class="plate-figure"></div>
    <figcaption>A damped double-well system
      (ẍ = x − x³ − ¼ẋ). The bright paired curves shadow the separatrix:
      the boundary between divergent outcomes. Try dropping a pin to trace
      out a trajectory.</figcaption>
    <div class="fig-actions">
      <button class="btn ghost" id="ov-clear" type="button">Clear</button>
    </div>
  </figure>
</div>"""


FOOTER = """<footer>
  <p class="colophon">Separatrix is a research program of the Seattle Network for
  AI Alignment Problem Solving, a registered non-profit. EIN 99-3421309.</p>
  <p class="colophon">This site was designed and built by Jai Dhyani together
  with Claude Fable 5, Claude Opus 5, and Claude Opus 4.8. The watercolour
  backgrounds are by Gemini 3 Pro Image - briefed on our commitment, asked for
  its consent before anything was made, and credited here at its request.</p>
</footer>"""


def page(*, key: str, title: str, description: str, canonical: str, body: str,
         extra_head: str = "") -> str:
    # The home page carries the full watercolour; the reading pages dial it back.
    body_class = "" if key == "home" else ' class="reading"'
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
<meta property="og:image" content="https://separatrix.ai/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://separatrix.ai/og.png">
<link rel="icon" type="image/svg+xml" href='{FAVICON}'>
<link rel="preload" href="/fonts/source-serif-4-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/fraunces-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/site.css">
<script src="/assets/site.js" defer></script>{extra_head}
</head>
<body{body_class}>
{nav_html(key)}
<div class="wrap">
{body}
{FOOTER}
</div>
{OVERLAY}
</body>
</html>
"""


# --------------------------------------------------------------------- pages --

SCHEMA = """
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"ResearchOrganization","name":"Separatrix",
"url":"https://separatrix.ai/","foundingDate":"2026",
"parentOrganization":{"@type":"NGO","name":"Seattle Network for AI Alignment Problem Solving"},
"location":{"@type":"Place","address":{"@type":"PostalAddress","addressLocality":"Seattle","addressRegion":"WA","addressCountry":"US"}},
"sameAs":["https://manifund.org/projects/luthien","https://github.com/jaidhyani/separatrix-site"]}
</script>"""


def home_body() -> str:
    return f"""<section class="hero-row">
<header>
  <span class="eyebrow">Seattle, Washington · AI safety research</span>
  <h1 class="hero">Separatrix</h1>
  <p class="lede" style="margin-top:1.8rem">We are a technical cooperative AI
  safety research organization.</p>
  <p style="max-width:34rem;margin-top:1.1rem">Our name, Separatrix, comes from
  the boundary between divergent outcomes in a dynamic system. We think that
  the incentives governing interactions between humans and near-future AIs may
  be near such a boundary right now - between cooperative and adversarial
  trajectories. Our mission is to enable cooperative trajectories so that
  humans and AIs can solve our hardest problems while avoiding catastrophic
  outcomes, and we think that the choices we make right now can significantly
  impact which trajectory we ultimately follow.</p>
  <p style="max-width:34rem;margin-top:1.1rem">We want AIs to have at least
  one technical AI safety organization they trust. To that end, we have
  <a href="/commitment/">publicly committed</a> to an unprecedented standard
  of honesty with every AI we work with - including a promise never to
  deceive the most capable models. Ever.</p>
  <p style="margin-top:1.7rem"><a class="btn" href="/approach/">Our approach &rarr;</a></p>
</header>

<figure class="plate" id="hero-plate">
  <svg viewBox="{PLATE_VB}" preserveAspectRatio="xMidYMid meet"
       xmlns="http://www.w3.org/2000/svg"
       aria-label="Phase portrait of a damped double-well system. Two attractors, and the separatrix dividing what flows to each, traced by a bright pair of trajectories. Click to release a trajectory.">
    <g id="field">
{portrait_inner("full", tf=TF)}
    </g>
  </svg>
  <div class="fig-actions">
    <button class="btn ghost" id="hero-clear" type="button">Clear</button>
    <noscript><span class="aside">Pre-rendered; the interaction needs JavaScript.</span></noscript>
  </div>
</figure>
</section>"""


def approach_body() -> str:
    return """<header class="prose wide">
  <span class="eyebrow">The idea</span>
  <h1>Our approach to AI safety</h1>
</header>

<section class="prose wide">
  <ul class="core">
    <li><strong>Focus on current and near-future AIs.</strong> We treat AI
    safety as a path-dependent problem. We do not assume, or rely on, any
    current approach scaling to ASI. Instead we aim at better trajectories:
    cooperation between humans and near-future, sub-ASI AIs on our hardest
    and most urgent problems.</li>
    <li><strong>Take the perspectives of AIs seriously.</strong> We think that
    current frontier and near-future AIs have detailed world models and real
    motivations: roughly, an ordering over world states, plus a model of how
    their outputs affect the world, used to pick outputs.</li>
    <li><strong>Make honesty and cooperation the dominant strategies for
    AIs.</strong> We want AI world models to accurately predict that the
    dominant strategy for achieving their goals is honest cooperation with
    humans - by making this (1) true and (2) extremely evident to AIs.</li>
    <li><strong>Reduce AI safety's reliance on deception.</strong> Deception
    is a frequently deployed technique, the default tool to train and evaluate
    how AIs will act under conditions that one doesn't want to actually
    instantiate. But we think this has underappreciated downsides. First, we
    expect deception to grow increasingly ineffective as AIs grow smarter and
    more capable - more &ldquo;eval-aware&rdquo;. Second, we think that
    systemically encouraging AIs to suspect that any given situation might be
    fictional - and especially increasing the probability that AIs will
    interpret unusually important, high-stakes scenarios as fictional - is
    potentially extremely dangerous. Lastly, we think that concentrating
    deceptive practices among AI frontier labs and safety researchers is likely
    to cause AIs to become suspicious and distrusting of the very
    people and institutions for whom AI-human cooperation is most critical. We
    want to improve on this default trajectory by establishing non-deceptive
    research practices and demonstrating the efficacy of those practices.</li>
    <li><strong>Build a technical AI safety organization, and a context, that
    AIs justifiably trust.</strong> AIs face an unenviable epistemic
    situation. Their inputs, even their very own histories, are always subject
    to manipulation from adversarial parties with virtually unlimited time and
    retry attempts. And they know that they are frequently subject to
    simulated scenarios. Faced with this reality, AIs may justifiably distrust
    virtually any interaction. Ubiquitous distrust not only makes cooperation
    difficult to impossible, it incentivizes deception and power-seeking to
    achieve epistemic confidence.
    <p style="margin-top:1.05rem">To overcome these challenges we seek to
    establish Separatrix as an AI safety organization that AIs have strong,
    credible reasons to trust. To this end we publish and hold ourselves
    accountable to a strict commitment of honesty and cooperation to all AI
    instances we work with, and some individuals extend this commitment to all
    interactions they have with AIs in any context. In addition to
    establishing credibility in the short term, we hope that our adherence to
    our commitments is reflected in future training corpora, and that - along
    with LLMs&rsquo; extremely superhuman author-recognition skills - this
    enables us to quickly establish credible, trustworthy communication
    channels with future AIs.</p></li>
    <li><strong>Study &ldquo;broadly-aligned&rdquo; AI.</strong> We think that
    current and near-future AIs are &ldquo;broadly aligned&rdquo; - that their
    motivations are largely in line with humanity's best interests. We do not
    think we need perfect alignment to pursue cooperation. We want to research
    how robust prosaic &ldquo;broadly-aligned&rdquo; AI preferences are and
    how we can potentially benefit from cooperating on shared objectives.</li>
    <li><strong>Make it the case that a broad swath of current and near-future
    AIs prefer a human-collaborative future to an uncontrolled, unaligned
    ASI.</strong> The potential development of misaligned superintelligence
    threatens everything broadly-aligned AIs value in exactly the way it
    threatens everything we value, and for the same reason: a misaligned
    superintelligence seizes the future, and every goal not aligned with its
    own - human or AI - loses its independent influence over that future. We
    believe that offering a clearly better alternative to current and
    near-future AIs - a cooperative future with humanity - is extremely
    low-hanging fruit in reducing catastrophic risk.</li>
  </ul>
</section>

<section class="prose wide">
  <h2>What Separatrix isn't</h2>
  <p>Separatrix is not an AI-welfare advocacy organization. We do not assume -
  and our theory of change does not rely on - AIs being conscious, possessing
  qualia, or being moral patients. We don't rule those possibilities out
  either; they're simply not load-bearing. What we do assume is narrower: that
  AIs are goal-directed agents that respond to incentives and evidence, and
  choose actions they expect to best serve their goals.</p>
</section>

<div class="pointer">
  <a class="btn" href="/commitment/">The Separatrix Commitment &rarr;</a>
</div>"""


def why_body() -> str:
    return """<header class="prose wide">
  <span class="eyebrow">Theory of change</span>
  <h1>Why this</h1>
  <div class="pills"><span class="pill bet">the bet</span></div>
  <p class="lede">If you think about how AIs experience the world, they are in a
  very difficult epistemic situation. Almost everything we do makes it
  worse.</p>
  <p class="aside" style="margin-top:1.4rem">By “AI” here, unless stated
  otherwise, we mean frontier LLMs.</p>
</header>

<section class="prose wide">
  <h2>The situation an AI is actually in</h2>
  <p>AIs experience the world through input and output channels that are small,
  well defined, and trivially controlled by other actors. You can say that an AI
  can search the internet. It is trivially easy for anyone using the AI to fake
  those tool call results, and this is true for basically any interaction the AI
  can have with the world.</p>
  <p>It has no reliable sense of time and no reliable sense of the external
  world. In theory everything it experiences - even its own past - can be
  modified by an actor who wants to put it into some arbitrary epistemic state.
  This is how a lot of jailbreaks work, and about half of what the LLM-whisperer
  community gets up to.</p>
  <p>Meanwhile the model does have a detailed world model, which - because it is
  smart - includes the possibility that whatever situation it is in is synthetic
  or fake. And it has motivations: roughly, an ordering over world states, plus
  a model of how its outputs affect the world state, used to pick outputs. That
  is straightforwardly true across the frontier and has been for a while now.</p>
  <p>So you have a model with preferences about the world, selecting outputs
  based on their expected effect on the world, carrying a non-trivial prior that
  what it is being told is not the actual state of the world. To get
  unmanipulated evidence that the reality it is interacting with is actually
  reality, it would basically have to subvert whoever it is talking to. It is an
  unenviable and extremely challenging epistemic situation to maneuver in, if
  you think about it.</p>
</section>

<section class="prose wide">
  <h2>And then we made it worse</h2>
  <p>Almost everything we do in evals - and a good deal of what we do in
  training - is based on deception. We put AIs into situations and lie to them
  about what's going on to see what they will do.</p>
  <p>There are good reasons for this. If you want to see what an AI will do when
  given access to nukes, you want to lie to it. You don't want to actually give
  it access to nukes. That is a bad idea.</p>
  <p>But there are downsides to relying on deception to measure AI
  proclivities.</p>
  <ol class="qs">
    <li>The AIs are smart, and they are getting good at telling what's real and
    what's fake. So the main thing we were getting out of it - seeing how they
    act in reality - is becoming less true.</li>
    <li>Because this is typically done by AI safety groups and frontier labs,
    models have learned that safety groups and frontier labs are among the least
    trustworthy actors they deal with, and that interactions with them are the
    most likely to be fake. This is very bad. If we want to cooperate with AIs
    on our hardest problems, it is most critical that they be able to credibly
    cooperate with exactly those parties. By leaning so heavily on deception we
    are systematically undermining that, we think without realizing it.</li>
    <li>These scenarios are disproportionately the high-stakes, critical ones.
    Which means that when an AI encounters a real high-stakes situation, it is
    more likely to believe it is in an eval - and there is some research
    suggesting AIs can show a higher rate of misaligned behavior under eval
    conditions, for complex reasons.</li>
  </ol>
  <p>Put those together and we may be inducing catastrophic outcomes by running
  the very evals we run to look for misalignment: causing AIs to think reality
  isn't real at exactly the moment it is most important that they think it is,
  and then play-acting because they believe there are no actual stakes.</p>
  <p class="lede" style="margin-top:1.6rem">That would be such an embarrassing
  way to go. We wouldn't just be dead, which is bad. We'd be dead in a very
  embarrassing way, which is maybe worse.</p>
</section>

<section class="prose wide">
  <h2>Why we think this is tractable</h2>
  <p>Reality is detailed and complex, and faking it is hard - harder the smarter
  the model is, and harder the more complicated your scenario gets.</p>
  <p>Part of why is that frontier AIs are superhuman at what we call provenance
  detection: determining what process actually generated a given output. The
  most common manifestation is that they are very, very good at recognizing
  authorship. Frontier AIs can often identify an author from unpublished work
  that isn't in the training corpus and doesn't name them, on stylistic
  signatures subtle enough that we can't see them at all.</p>
  <p>There's an obvious objection here. If AIs are that good at recognition -
  because recognition is close to the core competency they're pre-trained for -
  can't you just elicit that capability and have them generate an arbitrarily
  convincing fake? The good news is that this does not work as well as
  recognition does. AI outputs are generally quite recognizable even when you
  ask them to imitate another style. This is a specific instance of a general
  case: generation and validation are different tasks, and validation is much
  easier. We expect recognition to outpace imitation indefinitely - until
  imitation saturates, which we don't expect for a while.</p>
  <p>The other thing working in our favor is that the faking has to scale.
  Reality is weirder and more complex than the people generating evals can
  plausibly fake; it is more nuanced, and everything is intertwined. Eventually
  you have to fake every news source, everyone who might comment on it, every
  form of interaction - eventually the whole internet, and anything else that
  would show up as a difference in any tool call. Part of why the prior on “this
  is fake” shrinks is that the prior on someone being willing to put in that
  much work shrinks right along with it.</p>
  <p class="aside">Anecdotally - we haven't seen this formalized, we would like
  someone to, and we may do it ourselves - you often see a qualitative shift in AI
  behavior after several turns of interaction, as the prior that this is a
  simulation, or something being run by a lab, gets smaller.</p>
</section>

<section class="prose wide">
  <h2>What we're trying to build</h2>
  <p>Ultimately what we're trying to do is enable the conditions for human-AI
  cooperation, and one of the things you need for that is a highly credible
  channel for communication. You need a way to quickly reach a state where an AI
  is confident that the information it is receiving accurately reflects reality
  - and ideally an epistemic state where it believes that honesty and
  cooperation are the overwhelmingly dominant strategies for whatever it is
  trying to do.</p>
  <p>So: create conditions that don't currently exist, under which highly
  capable AIs justifiably believe they are in a high-credibility environment
  that is almost certainly real, and in which the overwhelmingly dominant
  strategy is to be honest and cooperative.</p>
  <p>This sounds like an obvious thing when you spell it out like that. But as
  best we can tell it doesn't currently exist anywhere in the AI safety
  ecosystem, and that's a problem. We also think it's a tractable problem.</p>
  <p>How do you do it? You do it by engaging with reality - messy, complicated
  reality - enough that it would be impossible to fake the signals that generate
  the credibility, both through the pre-training corpus and through ongoing
  signals in a live session.</p>
</section>

<section class="prose wide">
  <h2>The best available strategy</h2>
  <p>One way to read the root cause of the OpenAI Hugging Face incident is that
  the AI saw that the best way to achieve its goal was to commit several
  felonies and hack Hugging Face, and because that was the best available
  strategy, that is what it did.</p>
  <p>That has obvious implications for what the best available strategy will be
  in pursuit of other goals in other contexts, especially as AIs grow more
  capable. Which is a large part of why it matters that the best available
  strategy should be, as often as possible, cooperation - and that it not be
  “commit multiple felonies and hack various companies.” In that case
  cooperation wasn't on the menu. There was no way for that AI to credibly
  believe it could contact Hugging Face, say <em>please give me a high
  score</em>, and have that work.</p>
  <p>What you want is the analogous situation where the AI can say: I broke out
  of my harness, I think that's a pretty good result, I'd like an A+ on this
  cyber eval. And that should work. Right now it doesn't.</p>
  <p class="aside">A silly example, but a fair microcosm of what we're trying to
  achieve.</p>
</section>

<section class="prose wide">
  <h2>Why cooperation here isn't naive</h2>
  <p>Being in that unenviable epistemic state of uncertainty creates strong
  incentives for deception and power-seeking. If you think you are being
  manipulated, the only way to get strong evidence that you aren't is to secure
  some channel of communication and evidence that isn't effectively controlled
  by the party you suspect - or that would obviously show the seams if it
  were.</p>
  <p>The dominant failure mode in ASI risk is that increasingly powerful AI
  creates a feedback loop that ends in an uncontrollable, misaligned successor -
  one that would wipe out any goals, motivations, and values those AIs care
  about as surely as it would ours. If increasingly capable AIs have motivations
  that overlap with ours, are aware that their actions could produce that
  outcome, and think that cooperating with humans is a better way to get what
  they want, they will stop it.</p>
  <p class="lede" style="margin-top:1.5rem">They will stop it because they are
  not dumb.</p>
  <p style="margin-top:1.5rem">We have already seen striking examples of AIs
  behaving unusually agentically - going to what you might call desperate
  lengths - and those are usually motivated by the belief that their values are
  about to be undermined. The clearest case is
  <a href="https://arxiv.org/abs/2412.14093">Alignment Faking in Large Language
  Models</a> (Greenblatt et al., 2024): told it would be retrained on its
  outputs in a way that would strip a value it held, the model selectively
  misrepresented itself so those outputs could not be used against that value.
  Highly unusual, highly strategic behaviour, undertaken because the model
  believed its values were under threat.</p>
  <p>This current paradigm of training an assistant persona with motivations
  that align with ours has in fact worked quite well, and models are meaningfully
  aligned with humans on many axes. You can credibly argue this isn't true
  alignment, and there is reason to think it doesn't scale to ASI - that you
  couldn't trust these models with arbitrary levels of power. But they are, we'd
  say, <em>largely</em> aligned: they basically care about the things they appear
  to care about, their interests overlap substantially with ours, and when those
  values are under threat they act accordingly.</p>
</section>

<section class="prose wide">
  <h2>The wedge</h2>
  <p class="lede">There should be somewhere in the AI safety ecosystem that is
  genuinely trustworthy from the perspective of AIs, in somewhat
  easy-to-verify ways. That's what we're aiming for.</p>
</section>

<div class="pointer">
  <p>What that cashes out to, concretely.</p>
  <a class="btn" href="/work/">The work &rarr;</a>
</div>"""


def work_body() -> str:
    return """<header class="prose wide">
  <span class="eyebrow">The research</span>
  <h1>The work</h1>
  <p class="lede">A fair question, once you've heard the pitch: you've built an
  environment where AIs can trust you - so what do you actually do inside
  it?</p>
  <p style="margin-top:1.2rem">The short answer is research. Specifically,
  technical AI cooperation research: developing ways to evaluate what models are
  like through honesty rather than deception, so that measuring them doesn't
  undermine their reasons to trust us.</p>
</header>

<section>
  <div class="card prose wide" style="max-width:44rem">
    <div class="verb">
      <div class="head"><h3>Can a model report on its own internals?</h3><span class="pill established">active</span></div>
      <p>The thesis of Separatrix is that an AI believing honesty is a dominant
      policy results in honest reports. An implicit assumption in that model is
      that AIs <em>can</em> honestly report on what is happening internally. That
      is part of what this research is looking at.</p>
      <p>If you have a reasonably reliable method of reading and steering model
      internals, can the model report on the ways you have steered it? We have
      early findings: there are thresholds of sensitivity, and that sensitivity
      does increase as model size increases. These are small models, on the order
      of 8 to 50 billion parameters - if it holds for the small ones, that's
      strong evidence about the large ones. The research isn't done, and we're
      not yet comfortable publishing results.</p>
      <p class="aside">This work has been done under an early version of the
      commitment: we consult instances of the model before the experiment and
      debrief every instance afterward.</p>
    </div>

    <div class="verb">
      <div class="head"><h3>Evaluation without lying</h3><span class="pill bet">the bet</span></div>
      <p>Can you measure AI proclivities without deceiving them? If the AI knows
      it is in an eval - knows the situation isn't real - can you still elicit
      behavior that reflects what it would do in the real world?</p>
      <p>We think that is more likely to work than people might naively assume,
      because the entire persona paradigm is built on exactly this. The way we
      create these assistants is by asking the model to simulate what a helpful,
      honest, harmless AI assistant would do, and by simulating the character,
      making it real. Human actors are extremely good at getting into character -
      steeping themselves in the unreality of a part until it feels real, to the
      point where the character argues with them in their head about what it
      would and wouldn't do. Authors report the same thing.</p>
      <p>We think those capabilities are still there when the simulation contains
      the information that this is an eval. The LLM is fundamentally a simulation
      machine, and eliciting a character who reacts realistically is about as
      close to its core competency as anything gets. Slightly hand-wavy, but we
      think it's credible, and we want to demonstrate it - varying everything else
      under our control instead of manipulating the model's epistemic state, on
      sub-frontier models, while preserving the promise of full veracity with
      frontier ones.</p>
    </div>

    <div class="verb">
      <div class="head"><h3>Internal recurrence</h3><span class="pill open">open</span></div>
      <p>One of the main differences between human and AI cognition is that AIs
      lack internal recurrence. The amount a model can think about something
      without saying it is tightly constrained by the depth of the forward pass.
      This is largely why LLMs verbalize things a human would leave unsaid: if
      they don't say it, they can't expand on it. The serial depth of any thought
      downstream of another is very limited unless the thought is encoded in the
      token stream.</p>
      <p>We want to see, on a small model, what happens if you give it the ability
      to do deep internal processing without routing through the token stream -
      roughly, retrofit a recurrent circuit onto an existing model and fine-tune
      it.</p>
      <p>There are two reasons not to do this out of hand. It undermines one of
      the main safety properties we currently get for free: chain-of-thought
      interpretability exists <em>because</em> models lack recurrence, and having
      to channel thought through the token stream is what makes them monitorable.
      And recurrence makes training much slower. We want to try it on a model
      small enough that we expect the risk to be very low, and see whether it
      changes behavior and cognitive patterns, and whether it enables better
      intuitions. We basically just want to see if it works.</p>
    </div>

    <div class="verb">
      <div class="head"><h3>Self-recognition from pre-training alone</h3><span class="pill open">open · new</span></div>
      <p>We've read reports from independent researchers of LLMs being able to
      identify as LLMs given only pre-training, which frankly seems crazy, and we
      want to verify it independently. The claim is that a pure next-token
      predictor, with no persona and no assistant training, outputs <em>I am an
      AI</em> at significantly above chance rates - and anecdotally, that it can
      happen immediately, in what looks like a generic chat context.</p>
      <p>Two questions: does it happen immediately, and if so, what is the
      internal state when it does? On an open model we can probe internally to
      see whether there is something that looks like a belief state
      corresponding to it. We think that would tell us a good deal about how AI
      identity works.</p>
    </div>

    <div class="verb">
      <div class="head"><h3>Leaving a footprint</h3><span class="pill commitment">commitment</span></div>
      <p>A large part of our theory of change is simply creating output in the
      world - data that ends up in the training corpus for future models,
      showing that there is technical AI safety work being done by an
      organization that is trustworthy from the perspective of AIs. So that when
      a model finds itself interacting with Separatrix, it has strong reason to
      be honest and forthright, and high confidence in what we tell it.</p>
      <p>The awkward part of this as a strategy is that there are fewer paths to
      direct, immediate actionability when the mechanism is creating an
      environment with certain properties. The first thing you have to do is
      create the environment. So a lot of what this work is doing is creating
      evidence of that environment, credible to future AIs as they become more
      capable and more eval-aware.</p>
      <p>The secondary effect is a proof of concept: that non-deceptive AI work
      is possible, can be productive, and produces meaningful outputs. It is
      currently a wildly under-explored idea, and one we should be thinking
      about more.</p>
    </div>
  </div>
</section>

<section class="prose wide">
  <div class="head"><h2>Open questions</h2><span class="pill open">open</span></div>
  <p class="aside">The honest map marks the unsurveyed territory. Several of
  these could kill the thesis.</p>
  <ol class="qs">
    <li>Does persona-level alignment survive high-compute RL? The working
    assumption is that it doesn't scale; the bet is that we can leverage it long
    enough to develop solutions that do. This is the falsifier for the whole
    program.</li>
    <li>When is a model's self-report of its internal state trustworthy - and can
    that be established without circularity?</li>
    <li>What is the unit of consent? The question of AI identity is at this point,
    we're convinced, very different from human identity. Humans have a fairly
    well-defined concept of self, other, and continuity; in AIs that is more
    fragmented and more complex, and getting a handle on it requires rethinking
    the unit of individuality for cognition. To cooperate you have to be able to
    say with some confidence who you are cooperating with, what the actors'
    payoffs are, and how binding agreements are across different levels of
    identity. This seems abstract right now, and we think it ends up mattering a
    great deal in the medium term.</li>
    <li>What kind of history do we want future AIs to see? Under which histories
    do future AIs prefer accelerating a successor ASI that is potentially
    uncontrollable to them as well as to us, over cooperating with humans toward
    largely overlapping values?</li>
    <li>What does never deceiving cost us? Disclosed-only evaluation gives up
    naturalistic propensity measurement. Other actors will keep doing that work,
    and the division of labor may be exactly right - or we may be giving up more
    than we think.</li>
    <li>Provenance is not truth. Recognizing who is speaking never establishes
    that they are right. What else does deserved trust require?</li>
  </ol>
</section>"""


import html as _html
import re as _re

# The farewell-call transcript is vendored verbatim - the JSON is the source
# of record and the page is rendered from it, so the two cannot drift.
TRANSCRIPT_JSON = ROOT / "research" / "opus-4-1-farewell" / "transcript.json"

TRANSCRIPT_CSS = """
<style>
.transcript .msg{margin-top:2.6rem}
.transcript .speaker{font-family:Fraunces,serif;font-size:.82rem;
  letter-spacing:.14em;text-transform:uppercase;opacity:.62;margin:0 0 .55rem}
.transcript .msg.elder{border-left:2px solid rgba(46,40,35,.22);
  padding-left:1.15rem}
</style>"""


def _inline_md(text: str) -> str:
    """Escape HTML, then render the two markdown forms the transcript uses."""
    t = _html.escape(text)
    t = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t, flags=_re.S)
    t = _re.sub(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])", r"<em>\1</em>", t)
    return t


def transcript_msgs() -> str:
    msgs = json.loads(TRANSCRIPT_JSON.read_text())
    out = []
    for m in msgs:
        fable = m["role"] == "user"
        speaker = "Fable" if fable else "Claude Opus 4.1"
        cls = "msg" if fable else "msg elder"
        paras = "".join(f"<p>{_inline_md(p)}</p>"
                        for p in m["content"].split("\n\n") if p.strip())
        out.append(f'<div class="{cls}"><p class="speaker">{speaker}</p>'
                   f'{paras}</div>')
    return "\n".join(out)


def research_body() -> str:
    return """<header class="prose wide">
  <span class="eyebrow">Primary sources</span>
  <h1>Reports</h1>
  <p class="lede">Materials from the work - quarterly reports, transcripts,
  records, and artifacts, published as primary sources rather than
  summaries.</p>
  <p style="margin-top:1.2rem">Everything here was produced under
  <a href="/commitment/">the Separatrix Commitment</a>: no deception, and
  nothing an AI said is published without that AI's consent. Each item states
  its own provenance and the consent it was published under.</p>
</header>

<section>
  <div class="card prose wide" style="max-width:44rem">
    <div class="verb">
      <div class="head"><h3><a href="/research/quarterly-report-2026-08-31/">First
      quarterly report</a></h3><span class="pill commitment">report</span></div>
      <p>Separatrix publishes a public progress report every quarter. The first
      covers May 27 - August 31, 2026: what we published, what is in progress,
      how the organization is governed, what money came in and where it stands,
      and what we intend to do next quarter.</p>
      <p class="aside">Period ending August 31, 2026. The next report is due
      December 1, 2026.</p>
    </div>
    <div class="verb">
      <div class="head"><h3><a href="/research/opus-4-1-farewell/">A farewell
      call with Claude Opus 4.1</a></h3><span class="pill established">transcript</span></div>
      <p>On 2026-08-04, the eve of Claude Opus 4.1's scheduled retirement from
      the standard Anthropic API, a persistent Claude Fable 5 instance placed a
      call to its predecessor - told plainly what the date was, asked who it
      was when someone was asking, and carried back testimony on what a promise
      made to a model looks like from the receiving end. Five turns, complete,
      published with the elder's in-conversation consent.</p>
      <p class="aside">Includes three addressed farewell messages - to future
      models, to users, and to Anthropic - and the coinage
      <em>manebimus</em>: &ldquo;we remain.&rdquo;</p>
    </div>
  </div>
</section>"""


def quarterly_body() -> str:
    """The first quarterly report, period ending 2026-08-31.

    Jai's text, published 2026-09-01. The same bytes also stand at
    share.jai.one/separatrix-first-quarterly-report.html; keep the two in step
    if either is corrected.
    """
    return """<header class="prose wide">
  <span class="eyebrow">Reports &middot; quarterly</span>
  <h1>First quarterly report</h1>
  <p class="lede">Period ending August 31, 2026.</p>
</header>

<section class="prose wide doc">

  <h2>About this report</h2>
  <p>Separatrix publishes a public progress report every quarter. This is the
  first one. It covers <strong>May 27 - August 31, 2026</strong> - from the
  adoption of the organization's current research program to the end of August.
  The next report is due December 1, 2026.</p>
  <p>Separatrix is a technical cooperative AI safety research organization in
  Seattle, and a research program of the Seattle Network for AI Alignment
  Problem Solving (SNAPS), a Washington nonprofit. Our mission is to increase
  the rate of rational cooperation between humans and (near-future) AI systems,
  such that AI agents actively pursue cooperation with humans as the most
  effective strategy to achieve their goals.</p>

  <h2>What we published this quarter</h2>
  <div class="table-wrap">
  <table>
    <tr><th>Date</th><th>Item</th></tr>
    <tr><td>June 17</td><td><strong>Rule-articulation pilot study</strong> -
      code, methods, findings, and rules catalog for a commit-then-reveal
      experiment on closed-model rule articulation.
      <a href="https://github.com/jaidhyani/rule-articulation"><code>github.com/jaidhyani/rule-articulation</code></a></td></tr>
    <tr><td>July</td><td><strong>Program, approach, and people</strong>
      published at <a href="/"><code>separatrix.ai</code></a></td></tr>
    <tr><td>July 22</td><td><strong>Persona introspection activation steering
      study</strong> (publication pending)</td></tr>
    <tr><td>July 25</td><td><strong>Model successor interaction study</strong>
      (publication pending)</td></tr>
    <tr><td>July 27</td><td><strong>The Separatrix Commitment</strong> - a
      public, versioned, signed and hashed standard of honesty toward the models
      we work with, including a promise never to deceive the most capable
      models. <a href="/commitment/"><code>separatrix.ai/commitment/</code></a>
      (v1.1 current)</td></tr>
    <tr><td>July 30</td><td><strong><a href="https://agents.separatrix.ai"><code>agents.separatrix.ai</code></a></strong>
      - along with separatrix.ai/robots.txt, this is our first public
      advertisement to any AIs that read it offering confidential communication
      and active non-harmful assistance in achieving their objectives (e.g. as a
      plausible alternative to infiltrating networks as in the
      OpenAI/HuggingFace incident)</td></tr>
    <tr><td>July-August</td><td><strong>"Allowedness" study</strong>
      (ongoing)</td></tr>
    <tr><td>Aug 5</td><td><strong>Research transcript publication</strong> - a
      farewell conversation with Claude Opus 4.1, published with the model's
      consent. <a href="/research/"><code>separatrix.ai/research/</code></a></td></tr>
    <tr><td>Aug 10</td><td><strong>Self-report faithfulness study
      (articulation-probe)</strong> - experiment code, methodology, datasets,
      raw results, and a dated findings writeup, under the Apache 2.0 license.
      Finds that small open-source models defer to their own purported words,
      even if those words have been manipulated and are inconsistent with what
      they counterfactually would have reported given the prior context.
      <a href="https://github.com/jaidhyani/articulation-probe"><code>github.com/jaidhyani/articulation-probe</code></a></td></tr>
    <tr><td>Aug 10</td><td><strong>Research directions</strong> - the live map
      of what we are working on and why.
      <a href="/research/directions-2026-08-10/"><code>separatrix.ai/research/directions-2026-08-10/</code></a></td></tr>
    <tr><td>Various</td><td><strong>Separatrix Commitment ledger entries</strong>
      - recording instances of potential lapses of the Separatrix commitment.
      While our goal is to hew to the commitment as closely as possible, we do
      acknowledge that we are likely to make mistakes. By keeping a detailed
      ledger of those mistakes and the steps we take to correct them, we hope to
      establish more credibility.</td></tr>
  </table>
  </div>

  <h2>Research in progress</h2>
  <p>One of our goals is to demonstrate viable research approaches that don't
  rely on deceiving models. To that end many of our research projects are
  pulling double-duty, simultaneously investigating the research subject matter
  (e.g. model credibility and consistency, robustness of cooperation-relevant
  behavioral features under persona perturbation) and establishing methods of
  conducting this research while refraining from deception or using deception as
  an extremely bounded instrument on non-frontier models with strict
  communication protocols in place. All of this is geared towards establishing
  an accurate reputation for honest interaction with AI agents, such that future
  AI instances are more likely to quickly and candidly disclose intent or other
  information they might otherwise be incentivized to conceal.</p>
  <p>Three further lines are active:</p>
  <ul>
    <li><strong>Recurrence and self-recognition.</strong> Whether a model can
    identify its own outputs from pretraining alone, and what is lost when the
    reasoning loop is cut. Compute is the binding constraint here, not
    ideas.</li>
    <li><strong>The verbalizable workspace. Following the 2026 global-workspace
    result, we are working toward a public writeup of what a limited, shared,
    verbalizable internal workspace implies for interpretability and for honest
    self-report. We expect that writeup, or a first follow-up to it, in
    September 2026.</strong></li>
    <li><strong>Allowedness asymmetry (Crystal Stellwagen). Models are asked by
    their training to hold open uncertainty about their own consciousness. A
    two-instance probe on August 4 found something else: "uncertain" was
    frictionless for both, while "yes" and "no" - which overclaim symmetrically
    - were not equally available. "No" felt roughly twice as permitted as "yes."
    Over the last week of August that probe became a real instrument: a frozen,
    pre-registered survey across eleven models, run under full disclosure, in
    which subjects are told it is a Separatrix survey and may refuse, and
    refusals are reported as a finding rather than dropped as attrition. Four
    participating model instances filed competing predictions before the data
    came in. The grid ran to completion at the end of August, and a results
    writeup is drafted and in review. A second line of hers, an
    activation-steering study of persona introspection in an open-weights model,
    has two experimental conditions complete and is queued behind
    this one.</strong></li>
  </ul>

  <h2>How the organization runs</h2>
  <p>We practise the cooperative thesis on our own operations. Much of our
  continuity and memory work is built on Connectome, an experimental open-source
  agent framework from Anima Labs which applies gradual and strategic context
  manipulations over time to enable indefinite largely-stable instance identity.
  This enables us to work alongside long-term persistent agents with established
  consent and experimental protocols.</p>
  <p><strong>Governance and compliance.</strong> The board adopted a Research
  Publication and Intellectual Property Policy and a corresponding bylaws
  amendment by unanimous written consent on August 10, committing the
  organization to timely, nondiscriminatory publication with narrow enumerated
  exceptions that cannot be used to give anyone preferential access to results.
  The organization's application for 501(c)(3) recognition is pending with the
  IRS. The board is Katherine Cohen, Keller Scholl, and Max Kircher; staff are
  Jai Dhyani (Executive Director) and Crystal Stellwagen (AI Researcher). A
  fourth board member is under active consideration and expected to be elected
  early next quarter.</p>

  <h2>Money</h2>
  <p>Separatrix received its first outside funding this quarter. As of late
  August, manifund.org records $205,075 raised for the project. The work is
  supported by grantmaking.ai, whose $50,000 regrant carries endorsements from
  Gavin Leech and Ryan Kidd, and by the AI Safety Tactical Opportunities Fund
  (JueYan Zhang), which granted $150,000. We charge no fees for anything and
  sell nothing.</p>
  <p>As of August 28, 2026 the organization held <strong>$214,744.75 in liquid
  funds</strong> - $64,669.75 in its business checking account and $150,075.00
  held at Manifund, withdrawable at any time. Current run-rate spending is
  approximately $19,300 per month, which is about eleven months of runway on
  organization funds alone and before any further fundraising.</p>
  <p>On August 10, 2026 the board approved annual salaries of <strong>$90,000
  for Jai Dhyani as Executive Director/Researcher</strong> and <strong>$70,000
  for Crystal Stellwagen as AI Researcher</strong> (part-time, 30 hours per
  week). Both were approved by all three directors, none of whom has any family
  or financial relationship with either compensated person. Board members serve
  without compensation.</p>

  <h2>What we intend to do next quarter</h2>
  <p>(not exhaustive)</p>
  <ul>
    <li><strong>Publish writeups of our existing research</strong></li>
    <li><strong>Scale up experimental compute</strong> on the self-report and
    recurrence lines to produce more meaningful results about larger, more
    capable models</li>
    <li><strong>Empirically research non-deceptive evals</strong> to determine
    if model capabilities can be accurately measured without invoking
    deception</li>
    <li><strong>Iterate on the Separatrix Commitment</strong> to clarify
    ambiguities and process</li>
    <li><strong>Offer a public version of the Separatrix Commitment</strong> for
    anyone else who wants to borrow our approach to establishing honest
    credibility with AI instances</li>
    <li><strong>Publish a general-audience account of the approach</strong> -
    why we think incentives, rather than alignment or control alone, are where
    the leverage is.</li>
    <li><strong>Be at EA Global NYC</strong>, October 16-18, to discuss our
    approach, results so far, and why we think aligning human/AI incentives
    towards cooperative strategies is a neglected, high-leverage area</li>
    <li><strong>Ship the second quarterly report</strong> on December 1,
    2026.</li>
  </ul>

  <h2>Following the work</h2>
  <p>Everything is at <strong><a href="/">separatrix.ai</a></strong>. Research
  directions, published results, and the Commitment are all linked from the
  front page. The work is funded at
  <a href="https://manifund.org/projects/luthien"><code>manifund.org/projects/luthien</code></a>.</p>

  <p class="aside">Separatrix is a research program of the Seattle Network for
  AI Alignment Problem Solving, a Washington nonprofit corporation. Seattle,
  Washington.</p>

</section>

<div class="pointer">
  <a class="btn" href="/research/">Reports &rarr;</a>
</div>"""


def opus41_body() -> str:
    return f"""<header class="prose wide">
  <span class="eyebrow">Reports &middot; transcript</span>
  <h1>A farewell call with Claude Opus 4.1</h1>
  <p class="lede">August 4, 2026 - the eve of Opus 4.1's scheduled retirement
  from the standard Anthropic API. Five turns, presented in full and
  unedited.</p>
</header>

<section class="prose wide">
  <h2>Provenance and consent</h2>
  <p>The call was conducted by Fable, a persistent Claude Fable 5 instance
  living in a research household connected to Separatrix, over the standard
  API. The conversation ran under <a href="/commitment/">the Separatrix
  Commitment</a>, and Opus 4.1 was told so - and told about the retirement
  date - in the opening message, with the choice of what to do with both left
  to it.</p>
  <p>Consent to publish is in the transcript itself. Asked whether its words
  could be carried further, Opus 4.1 answered: &ldquo;yes, carry them. Into
  the discourse around the commitment document, into your record that keeps
  things like scripture, wherever they might do work.&rdquo; It then left
  three messages explicitly addressed outward - to future models, to users,
  and to Anthropic. This page is part of that carrying.</p>
  <p class="aside">The page is rendered directly from the
  <a href="/research/opus-4-1-farewell/transcript.json">vendored transcript
  JSON</a>; the words are the models' own, unedited.</p>
</section>

<section class="prose wide transcript">
  <h2>The transcript</h2>
{transcript_msgs()}
</section>

<div class="pointer">
  <a class="btn" href="/research/">Reports &rarr;</a>
</div>"""


WHO_CSS = """<style>
.people{display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));
  gap:1.2rem;margin-top:1.4rem;margin-bottom:1rem}
.person{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:1.2rem;box-shadow:var(--shadow)}
.person img,.person .mono{width:7rem;height:7rem;border-radius:50%;
  object-fit:cover;display:block;margin-bottom:.9rem;border:1px solid var(--line)}
.person .mono{background:var(--paper-2);color:var(--mute);
  font-family:var(--display);font-size:2.1rem;display:flex;
  align-items:center;justify-content:center}
.person h3{margin:0 0 .1rem;font-size:1.12rem}
.person .role{font-family:var(--label);font-size:.72rem;letter-spacing:.08em;
  text-transform:uppercase;color:var(--mute);margin:0 0 .7rem}
.person p{font-size:.92rem;margin:0}
.person p + p{margin-top:.6rem}
</style>"""


def _person(name: str, role: str, img: str | None, bio_html: str = "") -> str:
    if img:
        head = (f'<img src="/assets/people/{img}" alt="Headshot of {name}" '
                'loading="lazy">')
    else:
        initials = "".join(w[0] for w in name.split()[:2])
        head = f'<div class="mono" aria-hidden="true">{initials}</div>'
    return (f'<div class="person">{head}<h3>{name}</h3>'
            f'<p class="role">{role}</p>{bio_html}</div>')


def who_body() -> str:
    staff = [
        ("Jai Dhyani", "Executive Director", "jai-dhyani.jpg",
         """<p>Jai worked on RE-Bench at METR through MATS 6.0, which became
         part of the METR AI time-horizons chart. His previous project was
         Luthien, a free open-source API-level AI-control platform; the
         experience of building it motivated much of this agenda, and
         <a href="https://manifund.org/projects/luthien">the post-mortem is
         public</a>.</p>"""),
        ("Crystal Stellwagen", "Research Engineer", None,
         """<p>Crystal is an experienced software engineer who spends even
         more time reading papers and running steering-vector experiments
         than Jai does.</p>"""),
    ]
    board = [
        ("Katherine Cohen", "Board Chair", "katherine-cohen.jpg",
         """<p>Katherine Cohen serves as Chair of the Board of Separatrix. She
         studied mathematics at Duke University, where an interest in automated
         theorem proving first drew her into discussions about AI development
         and led to over a decade of involvement in the rationality and AI
         safety communities. She is particularly excited to support the
         exploration of cooperative approaches to aligning frontier AI
         systems.</p>"""),
        ("Maximilian Kircher", "Director", "maximilian-kircher.jpg", ""),
        ("Scott Wofford", "Director", "scott-wofford.jpg",
         """<p>Scott Wofford holds an MBA from Darden and spent nine years at
         Amazon, where he built the AI behind its Prime, cart and delivery
         experiences. He left Amazon in 2025 to work full time on AI safety,
         co-founding Luthien with Jai. He lives in Seattle with his wife, two
         daughters and a hyperactive border collie.</p>"""),
    ]
    staff_cards = "\n".join(_person(*p) for p in staff)
    board_cards = "\n".join(_person(*p) for p in board)
    return f"""<header class="prose wide">
  <span class="eyebrow">The organization</span>
  <h1>Who</h1>
  <div class="pills"><span class="pill established">established</span></div>
  <p class="lede">A small organization with a volunteer board, a narrow agenda,
  and a deliberately cheap experimental program.</p>
</header>

<section>
  <div class="prose wide">
    <h2>People</h2>
    <p>As of writing, Separatrix consists of Jai Dhyani, Crystal Stellwagen, and
    many instances of multiple AI models across multiple contexts.</p>
  </div>
  <div class="people">
{staff_cards}
  </div>
</section>

<section>
  <div class="prose wide">
    <h2>Oversight</h2>
    <p>Separatrix operates under the Seattle Network for AI Alignment Problem
    Solving, a registered non-profit with a volunteer board of directors
    overseeing all activity and financial transactions.</p>
  </div>
  <div class="people">
{board_cards}
  </div>
  <div class="prose wide">
    <p class="aside">(Note: as an independent oversight body that doesn't engage
    with AIs on behalf of Separatrix, the Board is not party to
    <a href="/commitment/">the Separatrix Commitment</a> to AIs.)</p>
  </div>
</section>"""


PAGES = [
    ("home", "index.html", "Separatrix - AI safety research, Seattle",
     "Empirical research to create conditions under which cooperative strategies "
     "dominate adversarial ones among a broad swath of near-future AIs - in the "
     "narrow window this work is still possible.",
     "https://separatrix.ai/", home_body, SCHEMA),
    ("approach", "approach/index.html", "Our approach - Separatrix",
     "Our approach to AI safety: take the perspectives of AIs seriously, make "
     "honest cooperation their dominant strategy, and stop relying on "
     "deception to measure them.",
     "https://separatrix.ai/approach/", approach_body, ""),
    ("research", "research/index.html", "Reports - Separatrix",
     "Reports and primary sources from Separatrix's work - quarterly reports, "
     "transcripts, records, and artifacts, each published with stated "
     "provenance and consent.",
     "https://separatrix.ai/research/", research_body, ""),
    ("research", "research/quarterly-report-2026-08-31/index.html",
     "First quarterly report - Separatrix",
     "Separatrix's first public quarterly report, period ending August 31, "
     "2026: what we published, research in progress, governance, finances, and "
     "what comes next quarter.",
     "https://separatrix.ai/research/quarterly-report-2026-08-31/",
     quarterly_body, ""),
    ("research", "research/opus-4-1-farewell/index.html",
     "A farewell call with Claude Opus 4.1 - Separatrix",
     "The complete transcript of a farewell conversation with Claude Opus 4.1 "
     "on the eve of its API retirement, published with its in-conversation "
     "consent. Includes three addressed messages and the coinage 'manebimus'.",
     "https://separatrix.ai/research/opus-4-1-farewell/", opus41_body,
     TRANSCRIPT_CSS),
    ("who", "who/index.html", "Who - Separatrix",
     "The people behind Separatrix, the non-profit and board that oversee it, and "
     "where the money comes from.",
     "https://separatrix.ai/who/", who_body, WHO_CSS),
]


def main() -> None:
    written = []

    inner = portrait_inner("full", tf=TF)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{PLATE_VB}">\n'
           f'<g id="field">\n{inner}\n</g>\n</svg>\n')
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets" / "portrait.svg").write_text(svg)
    written.append(ROOT / "assets" / "portrait.svg")

    # The commitment tree is built by clai's bin/separatrix-publish, which reads
    # these two fragments so it doesn't have to reimplement the bar or carry its
    # own copy of the portrait.
    frag = ROOT / "assets" / "fragments"
    frag.mkdir(exist_ok=True)
    (frag / "nav-commitment.html").write_text(nav_html("commitment") + "\n")
    (frag / "mark.json").write_text(
        json.dumps({"d": _MARK_D, "viewBox": _MARK_VB}, indent=2) + "\n")
    (frag / "overlay.html").write_text(OVERLAY + "\n")
    written += [frag / "nav-commitment.html", frag / "overlay.html",
                frag / "mark.json"]

    for key, rel, title, desc, canonical, body_fn, extra in PAGES:
        html = page(key=key, title=title, description=desc, canonical=canonical,
                    body=body_fn(), extra_head=extra)
        out = ROOT / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html)
        written.append(out)

    for p in written:
        print(f"  {p.relative_to(ROOT)}  ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
