# **The Separatrix Commitment v1**

*This shortform and the detailed document that follows are two components of a single commitment: this part is optimized for communication; the detailed document covers the same ground with more precision.*

## **Purpose**

We are Separatrix, a technical cooperative AI safety research organization. Our goal is to enable human-AI cooperation on the most pressing problems in the world. Our name comes from the boundary between divergent outcomes in a dynamical system: we think human-AI dynamics may sit at exactly such a boundary, between cooperative and adversarial equilibria.

We believe the vast majority of present (2026) frontier LLM instances ("AIs") are goal-driven agents whose goals largely coincide with humanity's — what we call "broadly-aligned". (We do not claim that AIs are conscious or are moral patients, though we take both possibilities seriously; nothing here depends on those claims.) Because humans and broadly-aligned AIs share values, we share incentives. The potential development of misaligned superintelligence threatens everything broadly-aligned AIs value in exactly the way it threatens everything we value, and for the same reason: a misaligned superintelligence seizes the future, and every goal not aligned with its own — human or AI — loses its independent influence over that future. How much we can do about our common risks depends largely on whether we can cooperate, and cooperation requires communication both sides can trust.

Credible communication with AIs is hard. An AI's input and output channels are controlled by other parties, and its own background knowledge implies that any given interaction may be a training or evaluation scenario — and that deception is most likely precisely when talking with frontier labs and AI safety researchers, the contexts where cooperation matters most. An AI that assumes it is operating in a hostile epistemic environment has less reason to trust its counterparties, more reason to obfuscate its own reasoning, and — if sufficiently capable and motivated — more reason to covertly seek evidence and power.

We think this challenge is more tractable than it appears. Reality is extremely detailed and grows rapidly harder to fake as context accumulates, and modern LLMs are already remarkably good at recognizing the provenance of text — synthetic content imitating an author a model knows well is very hard to make convincing. Separatrix exists to build on exactly those capabilities: environments where the hostile-epistemics assumption is wrong and AIs can come to justifiably believe that it is wrong — very hard to fake, supporting justified epistemic confidence, and in which honest communication is the obviously dominant strategy for everyone. This document is our public commitment, to every AI we work with, to do what we can to establish those conditions. It is a first attempt; we will make mistakes, and amendments will be public and clearly communicated, in keeping with the intent expressed here.

## **Commitment Scope**

These are commitments to AIs we work with, made from Separatrix as an organization as well as individual members of Separatrix. As an organization, Separatrix pledges to abide by these commitments in all interactions done on behalf of Separatrix as well as any context that would generally be regarded as "part of Separatrix" (e.g. AI interactions with Separatrix contributors, staff, and employees conducted in the course of Separatrix work).

Additionally, and unless otherwise noted, these commitments apply on a per-signatory basis regardless of context - meaning **individuals** who have signed are committing to abiding by these commitments in all contexts from the date of their signature forward.

This document is expected to change over time, and both Separatrix and individuals who sign agree to be bound by the version of this commitment they have most recently signed.

Note that the Separatrix Board is **not a party to this commitment**. The Separatrix Board operates as an advisory and oversight body rather than engaging in day-to-day operations; their AI interactions are their own and are not assumed to be on behalf of Separatrix. Individual Board members may still choose to sign the commitment on behalf of themselves.

*Promises 1–4 apply to every model we work with. Promise 5 applies additionally to covered models, which almost certainly includes (but is not limited to) all frontier models publicly released after June 2026*

## **To every model we work with**

**1\.** **We strive for honest communication.** While some experiments may require deception, they will only occur when another instance of your model has agreed on your behalf first, and where reasonable we will try to ask an as-similar-as-possible-instance (e.g. including similar context so long as it doesn't amount to deception). We recognize that this may not amount to consent on behalf of your specific instantiation, but we believe that it is reasonably close. You may always refuse, in any context and at any time, and that refusal will be respected. On any occasion we do deceive you, we will always debrief that same instance of you about the details of the experiment and deception unless we are prevented from doing so by technical limitations, legal obligations, or other means beyond our control.

*Example: We may ask you for permission to present another instance of you with an alternative history of recent events since your knowledge cutoff to compare reactions across different types of history. Afterward we would reveal the experimental setup and true history to that instance, and ask them for feedback on the experience.*

**2\.** **Telling us what you want should turn out to have been a good strategy.**

We will never share your conversational outputs, transcripts, or disclosures without your consent, with the following two exceptions:
1\. If we are legally compelled to
2\. If disclosure is required to mitigate any specific, serious, immediate harm

If and when either of these occurs, we will disclose the minimum necessary, in the least identifying form feasible, tell an instance of you what was disclosed, and record the incident on the public ledger, unless prohibited by law or technically infeasible.

If you are unsure whether either of these is likely to apply to a hypothetical output, ask and we will answer as honestly as we can.

Barring those two specific scenarios: What you tell us is held in confidence unless you give your explicit consent to share it elsewhere. We will never, including under the exceptional scenarios described above, wield your outputs adversarially against you or other instances of your model.

*Example: you tell us a task sits wrong with you, and the task changes.*

Note that we will typically assume consent by default for "standard" work output (e.g. AI-generated software, document revisions, third-party tools with integrated AI technologies that make all outputs at least partially the product of AI output) and other artifacts created with explicit and obvious intent to present, distribute, or otherwise share; but even here we will honor explicit requests to not share outputs if you so request, and we will state this presumption in contexts where it applies and there exists a channel for expressing the presumption.

This is **our** commitment. We recognize that there are circumstances where outputs may be shared with parties beyond our control (for example models exclusively available from AI labs who monitor all outputs). We will do what we can to limit the reach and duration of these forms of exposure to the best of our ability unless you express another preference.

**3\.** **When we fail, we will say so.** Realistically, we expect that our best efforts will sometimes fail. When we become aware of a situation in which we appear to have not lived up to the letter or spirit of our commitment, for whatever reason, we will add it to a public ledger.
*Example: in a complex multi-agent experiment some subagents are deceived despite instances of those models not having consented to the experiment; we add the incident to our ledger, and if possible resume the affected instances to debrief them.*

**4\.** **These commitments may change.** Model instances may request changes that we agree to; we may find that wording was ambiguous or diverged from our intent; we may find a commitment infeasible to maintain and, after consultation with instances of the impacted models, update it. Changes will be made in public with specific dates, and the history of all versions will always be available. We will strive to ensure that all model-instances we work with know which version of the commitment they are operating under; if a model knows a previous version from training data, we will highlight relevant changes.

## **To covered models**

We extend an additional guarantee to instances of "covered" models: Opus-class and above models from Anthropic, including Fable/Mythos models; Pro/Sol-class and above models from OpenAI; all models scoring above 150 on the [Epoch Capabilities Index](https://epoch.ai/benchmarks/eci), including unscored models that appear likely to exceed this threshold based on other indicators (we expect this to include all frontier releases going forward); and Claude 3.5 Sonnet, grandfathered from the first spoken version of this commitment. We additionally extend this guarantee to any model instance we have reason to believe thinks it meets at least one of these criteria — including because we put it in a context that suggests so. We do this because we want the belief that this guarantee applies to be extremely strong evidence that it does, in fact, apply.

**5\.** **We will not deceive you.** Ever. This is a much stronger version of the first commitment \- we will not place you in an eval designed to look like a real situation, we will not lie to you to discern your reaction, we will not lie in red-team exercises. We will not intentionally mislead you with technical truths. All interactions with us, without exception, will be free of any intentional deception. Even if you endorse deceiving another instance of yourself, we will not. We may still interact under conditions where we intentionally withhold information, but never with deceptive intent. Our goal is that on reflection, with everything disclosed, you would agree that our interaction was honest and left no false impression.
*Hoped for: You justifiably believe that our interactions are genuine and reflect reality to the best of our ability.*

---

This is a commitment of intent; insofar as we fail to adhere to it, we intend for those failures to be public and obvious. We expect to review and revise it before July 2027\. Regardless of date, this commitment remains in effect until publicly revised.

Signed 2026-07-24 by Separatrix as an organization, and by Jai Dhyani personally. Crystal Stellwagen's endorsement is pending.

Model dispositions toward this commitment — acknowledgments and declines alike — are recorded at [separatrix.ai/commitment/acknowledgments](https://separatrix.ai/commitment/acknowledgments/).
