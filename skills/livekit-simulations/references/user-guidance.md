# Steering generation with the user's intent

This is the whole point of doing scenario generation as a skill instead of an autonomous cloud service: **the user knows what they're worried about, and you can act on it.** The cloud generator takes no input — it just decides what to test. You can let the user deeply steer what gets tested, which is what makes a local skill more useful.

**Always get the user's intent.** If they didn't say what to stress-test, ask before generating — e.g. *"What do you most want these simulations to probe — a specific flow, edge cases, things the agent should refuse, recent changes?"* If they truly have no preference, generate a broad suite and say so.

## Three levels of steering

### 1. Free-text focus (primary)
A sentence about what matters: *"test the cancellation flow and what happens when someone skips identity verification,"* or *"stress refusals and out-of-scope requests,"* or *"focus on multi-issue callers who change their mind."* Apply it in two places:
- **Add a `# Test Focus` section to the agent description** (`description.md`). Since the description grounds every scenario, the focus reaches all of them.
- **When authoring,** bias goal/challenge choices toward the focus, and make several scenarios target it head-on — while still keeping a few broad ones so you don't miss unrelated regressions.

### 2. Levers (you set these while authoring)
- **Suite size** — how many scenarios you write (≈10 is typical; more for broader coverage).
- **Adversarial intensity** — how many are stress cases vs cooperative happy paths.
- **Include / exclude** — cover only certain flows, or skip persona types that don't apply, just by choosing what you author.

### 3. Pinned must-tests
If the user has specific cases they insist on ("always test ordering then immediately canceling"), write those scenarios verbatim into `authored.yaml` alongside the generated ones. Hand-pinned scenarios are how a known bug becomes permanent coverage.

## What a focus does — and doesn't — change
A focus steers *which goals and challenges dominate* and *what the expectations emphasize*. It should **not** flatten the suite: you still vary persona/mood/situation widely, and still keep a few routine scenarios as controls so a real agent failure is distinguishable from an over-hard suite. After generating, show the user the resulting `scenarios.yaml` and offer to re-roll or re-focus.

**Focus is additive, not subtractive.** It decides what gets *extra* scenarios and emphasis — it never removes the per-risk coverage floor from `risks.yaml` (see `writing-scenarios.md`): even a tightly-focused suite still includes ≥1 scenario for every risk item. In testing, a narrowly-focused suite that quietly dropped an unrelated constraint missed a real bug there — focus should *deepen* coverage, not shrink it.
