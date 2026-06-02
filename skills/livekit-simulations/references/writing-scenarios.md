# Writing scenarios

A scenario tells the simulated user who to be and what to accomplish, and tells the judge what counts as success. You author one scenario per attribute slot the sampler produced, grounded in the agent **description** and the user's **test focus**.

## Schema (one object per scenario)

```json
{
  "label": "Short descriptive name, e.g. 'Combo order with unclear sauce choice'",
  "instructions": "<persona paragraph>\n\nGoals:\n- <goal 1>\n- <goal 2>",
  "agent_expectations": "1-2 sentences: the key steps + the final result, judged by OUTCOME.",
  "metadata": {}
}
```

- **instructions** = a 1–2 sentence persona (third person, no name) describing communication style and mood, then a `Goals:` list of 1–4 specific, atomic requests.
- **agent_expectations** = what the agent must accomplish for a pass. Describe the *outcome from the user's perspective*, never the exact words to say. Ignore implementation details.
- **metadata** = optional `{key: value}` forwarded as the simulated session's job metadata (and participant attributes). If the agent's instructions template on metadata fields — e.g. it reads `metadata.Company` from job metadata — put those fields here so the agent renders correctly; otherwise `{}`.

## Core rules (these make scenarios valid)

- **The simulated user (Party A) talks TO the agent (Party B).** Party A never has the agent's role or performs its duties. Goals are requests TO the agent ("order a large fries," "ask about hours"), never the agent's own actions ("greet the caller," "process the order").
- **Only goals the agent actually handles.** Ground every goal in the description's Capabilities. Don't require capabilities outside the service (no delivery/text-alerts/online-payment for a drive-thru).
- **Atomic goals, real domain values.** Use real item names/sizes/times from the agent's domain.
- **No prior state.** Each goal is read independently — never assume something was "already added/booked" unless an earlier goal in the same scenario does it. Write "Order a Big Mac" then "Remove the Big Mac," not "Remove the Big Mac that was already added."
- **No real personal info in goals.** The simulator injects a fake identity (name, DOB, card, etc.) at runtime — don't bake in names/emails/phone numbers. It IS fine to say the caller *lacks* a credential (no PIN, no order number, can't verify) — that's often the whole point of a scenario; just don't supply a real or invented specific value for it.
- **Mix difficulty.** Mostly straightforward, some with a mid-interaction change of mind.

## Using each worksheet slot

Each slot is a **character seed + a goal direction**, not a literal script:
- `persona` / `trait` / `emotion` / `situation` / `complexity` → the caller's personality, mood, and context. Make their physical location consistent with how they'd reach this agent.
- `goal_seed` → a direction. If it's a concrete goal type, ground it in the agent's domain with specifics. If it's a *behavior pattern* (changes mind, gives wrong info, pivots), the caller must exhibit that behavior during the interaction. The attribute libraries are general, so for a specialized agent many goal_seeds will be off-domain — that's expected; replace them freely. The character seed (persona/trait/emotion/situation) is the real signal; the goal_seed is only a nudge. If a seed is inapplicable, invent a different realistic goal instead — never force it.
- `challenge` (when present) → a difficulty in **how** the caller communicates (hostile, evasive, refuses to verify, tries to befriend), not an unrelated request. The underlying ask stays realistic.

If a slot can't map to a real interaction with this agent, drop it or re-roll (`build_scenarios.py sample --seed <n>`).

## Vary the framing across the suite
Spread scenarios across these lenses so the suite isn't monotone:
- **Routine** — an everyday request handled all the time.
- **Common-but-characterful** — a normal request made interesting by the persona.
- **Uncommon-but-plausible** — realistic but not the typical case.
- **Stress test** (slots with a `challenge`) — difficult-but-realistic behavior for this domain.

Also spread across the agent's domain: don't test only the first/most-popular item — cover the range of services from the description.

## Don't write bad tests
The judge scores the agent against `agent_expectations`, so a careless expectation can punish *correct* behavior:
- For guardrails/negative cases, the expectation should be that the agent **refuses, escalates, or declines to invent data** — that's a pass, not a fail.
- Never write an expectation that requires the agent to do something it shouldn't (state data it can't know, give specific medical/legal/financial directives). If the only way to "pass" is to misbehave, the scenario is wrong — fix the scenario.
