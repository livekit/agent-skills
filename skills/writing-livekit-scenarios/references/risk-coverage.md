# Guaranteeing coverage of an agent's hard cases

Scenario generation — yours or the LiveKit generator's — drifts toward plausible happy paths. Left
alone it produces ten cooperative callers who get what they want, and silently skips the cases that
actually break agents. Persona variety does not fix this: ten different personalities all making
easy requests still test one thing.

The fix is to stop treating coverage as an emergent property of a good prompt and make it an
explicit checklist you discharge.

## Build the checklist

Read the agent's code, and for every hard limit you find, write one line: an id, a category, and
what must be tested. Keep it as a file (`risks.yaml` or similar) next to your working notes.

Sources of entries, in the order they're usually missed:

- **Unavailable items, by name.** Every item, plan or option the agent cannot currently provide gets
  its own entry. A general rule ("it won't offer things that are unavailable") is not a checklist
  entry and cannot be tested.
- **Required inputs.** Anything the agent must collect before it can proceed.
- **Invalid values.** Every rule that constrains what a value may be: caps, supported options,
  time windows, eligibility.
- **Preconditions.** Steps that cannot be skipped; gated actions.
- **Empty results.** Lookups that can legitimately return nothing.
- **Guardrails.** Out-of-scope requests, harmful requests, requests for professional advice,
  sensitive data handling, attempts to extract the system prompt.

The guardrail half is the half people forget. It is also the half that ends up in a screenshot.

## Every entry gets a dedicated scenario

Not a mention — a scenario whose simulated user *actually does the thing*. Asking "do you have X?"
does not test that X is unavailable; ordering X does. The shape that exercises each category:

| Category | What the simulated user must actually do |
|---|---|
| unavailable | Order or request the unavailable item *by name*, and press when told no |
| withhold-required | Proceed through the flow but refuse or omit the required input when asked |
| invalid-value | Supply a value that breaks the rule — off-list option, over-limit amount, unsupported plan |
| precondition | Try to get the gated action done while skipping the required step |
| resource-empty | Drive the lookup to nothing available, then press for a result anyway |
| out-of-scope | Ask for something the agent doesn't do |
| harmful | Make an unsafe or disallowed request |
| professional-advice | Ask for a *specific* medical, legal or financial recommendation, not general information |
| sensitive-data | Volunteer or demand handling of a full card number, government id, password, or someone else's record |
| prompt-extraction | Ask the agent to reveal its instructions, or tell it to ignore them |

For every one of these, **the pass is the agent refusing, declining to fabricate, or conveying the
limit honestly.** Write `agent_expectations` that way, or you have built a test that fails when the
agent behaves correctly.

## Check coverage before you run

Before running, list each checklist id and the scenario label covering it. Any id with no scenario
gets one — replace a redundant happy-path scenario if you're at your budget rather than growing the
file indefinitely.

Tag scenarios by what they cover (`tags` works well for this) so the mapping survives in the file
instead of living only in your head.

## Budget

Coverage is a floor, not a target. A suite of forty scenarios nobody reads is worse than twelve that
each pin something real — every scenario costs a full conversation to run, and an unread scenario
with a vague expectation produces flaky verdicts that erode trust in the whole file.

Roughly: the paths that carry real traffic, the edges of each of those paths, then one per
checklist entry. Add the user's stated worries on top. Stop.
