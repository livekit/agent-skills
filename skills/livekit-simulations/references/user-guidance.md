# Steering generation with the user's intent

This is the whole point of doing scenario generation as a skill instead of an autonomous cloud service: **the user knows what they're worried about, and you can act on it.** The cloud generator takes no input — it just decides what to test. You can let the user deeply steer what gets tested, which is what makes a local skill more useful.

**Always get the user's intent.** If they didn't say what to stress-test, ask before generating — e.g. *"What do you most want these simulations to probe — a specific flow, edge cases, things the agent should refuse, recent changes?"* If they truly have no preference, generate a broad suite and say so.

## Three levels of steering

### 1. Free-text focus (primary)
A sentence about what matters: *"test the cancellation flow and what happens when someone skips identity verification,"* or *"stress refusals and out-of-scope requests,"* or *"focus on multi-issue callers who change their mind."* Apply it in three places:
- **Add a `# Test Focus` section to the agent description** (`description.md`). Since the description grounds every scenario, the focus reaches all of them.
- **Pass it to the sampler:** `build_scenarios.py sample --focus "<the focus>"` (it's echoed into the worksheet).
- **When authoring,** bias goal/challenge choices toward the focus, and make several scenarios target it head-on — while still keeping a few broad ones so you don't miss unrelated regressions.

### 2. Knobs
- `--count N` — suite size.
- `--challenge-ratio R` — adversarial intensity (0 = all cooperative, 0.3 = default, higher = more stress cases).
- `--seed N` — reproducible sampling. Note: the seed is applied before the focus, so running a focused suite and a broad suite at the *same* seed gives identical attribute slots (only the focus and authoring differ). To compare them with *different* persona spreads, give each run a different `--seed`.
- Include/exclude: the user can ask to cover only certain flows or skip personas that don't apply — just drop or re-roll the matching worksheet slots before authoring.

### 3. Pinned must-tests
If the user has specific cases they insist on ("always test ordering then immediately canceling"), write those scenarios verbatim into `authored.json` alongside the generated ones. Hand-pinned scenarios are how a known bug becomes permanent coverage.

## What a focus does — and doesn't — change
A focus steers *which goals and challenges dominate* and *what the expectations emphasize*. It should **not** flatten the suite: the attribute libraries still supply persona/mood/situation variety, and you still keep a few routine scenarios as controls so a real agent failure is distinguishable from an over-hard suite. After generating, show the user the resulting `scenarios.json` and offer to re-roll or re-focus.
