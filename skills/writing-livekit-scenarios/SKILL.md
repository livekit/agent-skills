---
name: writing-livekit-scenarios
description: 'Creates and maintains the scenarios a LiveKit agent simulation runs, and wires the agent to consume them. Use when the user asks "what should I test", "generate simulation scenarios", "write scenarios for my agent", "add a scenario for X", "organize my scenario files", "my simulations are flaky", "the scenario hits my real database", "seed state per scenario", "it passed but booked the wrong thing", "grade the final state", or wants to stress-test a flow before shipping. Covers generating a baseline with the LiveKit scenario generator and refining it, authoring the cases generation misses, the instructions shapes that steer a simulated user reliably, splitting scenarios into sets across files, and the agent-side code that seeds deterministic state from a scenario and fails a run on its final state. To run them use running-livekit-simulations.'
license: MIT
metadata:
  author: livekit
  version: "1.0.0"
---

# Writing simulation scenarios

A scenario is a simulated user's **`instructions`** (who they are, what they want) plus
**`agent_expectations`** (what counts as success). A simulation plays the scenario against the real
agent and an LLM judge grades the transcript.

The scenarios are the durable artifact. Runs are disposable; a good scenario file is reviewed in a
diff, re-run for years, and is the only thing standing between a prompt edit and a silent
regression. That is what this skill is for.

Look up the exact file schema and CLI flags with `reading-livekit-docs` before writing a file —
field names and commands move, and this skill deliberately doesn't restate them. Conceptually a file
is a named group of scenarios; each scenario carries the simulated user's instructions, the pass
criteria, and optionally tags for grouping and per-scenario data the agent can read at runtime. If
the CLI offers to add stable per-scenario ids to a file, accept and commit them.

## Start from a generated baseline

Do not author from an empty file. LiveKit's generator reads the agent's source and produces a solid
first pass, much faster than writing ten scenarios by hand:

```bash
lk agent simulate text -n 10    # confirm the exact flags with --help
```

The CLI asks for confirmation first, because **generating from source uploads the code to LiveKit
Cloud** for the generator to read. Say so plainly before running it, and let the user decline —
some code can't leave the machine, and then you author manually instead. There is a flag to skip
the prompt for non-interactive runs.

When the run finishes, the CLI either tells you where it saved the generated scenarios or offers to
save them into the project. Either way, get that file into the repo as the starting point.

**The generator is good but not steerable yet.** It infers intent from code, so it produces
plausible conversations rather than the ones this agent's users actually have, and it has no way to
know what the user is worried about. So treat its output as a draft:

1. **Read every scenario.** Delete the ones that don't matter. A file you haven't read is not a
   test suite.
2. **Sharpen vague expectations.** `agent_expectations` that a judge can't decide produces verdicts
   that flip between runs. This is the single biggest cause of flaky scenarios.
3. **Add what generation misses.** It drifts to happy paths. See `references/risk-coverage.md` —
   turn the agent's constraints into a checklist and give each item a scenario.
4. **Fold in what the user actually fears.** Ask what they want stress-tested if they haven't said.
   That intent is the whole reason a human-steered suite beats an automatic one.

## Ask what to probe

The user knows which flow keeps breaking, which customer complained, which change they're nervous
about. Always capture that and let it bias the suite — more scenarios, deeper, on that surface.

Focus is **additive**. It deepens chosen areas; it never drops coverage of the agent's hard limits.
If the user genuinely has no preference, generate broad and say that's what you did.

## Ground scenarios in what the agent can actually do

Read the agent's code before authoring — locally, with your normal tools. You are looking for three
things: what a user can ask for (**capabilities**), where requests get blocked (**constraints**:
required steps, unavailable items by name, caps, eligibility), and what the agent must refuse.

Constraints matter most. A scenario asking for something the agent cannot do is only valid if its
expectation is that the agent *says so* — write it the other way round and you have a test that
fails when the agent behaves correctly.

Scope: the agent reachable from the session entrypoint, plus agents it hands off to and tasks it
awaits. Not other classes in the directory, not unused imports, not example files.

## Write instructions the simulated user can follow

Two shapes, chosen by what the scenario is for. Details and examples in
`references/scenario-craft.md`.

- **Point-form direction** for deterministic flows you'll grade on end state. A structured template
  — persona, opening line, facts revealed only when asked, steps in order, conditional reactions —
  keeps the persona model on rails and makes the run repeatable.
- **A persona paragraph plus goals** for open-ended and adversarial scenarios graded on the
  conversation alone, where you *want* the simulated user to improvise.

Either way: goals are requests *to* the agent, never the agent's own actions; use real values from
the agent's domain; assume no prior state; and vary persona, mood and difficulty across the suite so
it isn't ten versions of the same cooperative caller.

## Split scenarios into sets, one file per set

The run command takes one scenario file, so **a file is a run**. Split along the lines you actually want to run
separately — not by topic.

The axis that matters most is **how the set is graded**:

- Scenarios driving concrete tool flows to a deterministic end state, graded on final state *and*
  the conversation (see "Make the agent consume the scenario" below).
- Open-ended and adversarial scenarios graded on `agent_expectations` alone.

These want different instructions shapes, different agent wiring, and often different run cadence,
which is exactly why they belong in different files. The second axis is **cadence**: a small set
worth running before a merge versus the full set before a release.

Give each file a `name` that says what the set is, since that labels the run. Inside a file, use
`tags` to slice — `feature` so a failure points at the part of the agent that owns it, plus whatever
else you filter by (channel, difficulty). Keep a header comment recording the set's assumptions:
pinned dates, required environment variables, what its expectations depend on.

## Keep scenarios reproducible

A scenario that passes today and fails in March taught you nothing.

- **Write absolute dates**, and pin the agent's clock (typically an environment variable) so
  availability and expectations always line up. Relative dates rot.
- **Don't let scenarios hit real backends.** Seed deterministic state from the scenario instead —
  see "Make the agent consume the scenario" below.
- **Keep ids stable** where the CLI supports them. Labels and instructions change; the id is what
  correlates a scenario's runs over time. A scenario rewritten from scratch is a new scenario and
  gets a new id.

## Make the agent consume the scenario

Two things a scenario file can't fix on its own: a scenario that reaches a real backend grades
differently every run, and a judge that only reads the transcript passes a run that booked the wrong
room. Both are fixed in the agent's code, in one branch at the top of the entrypoint:

1. **Detect** a simulation from the job context; in production the check comes back empty and
   nothing else changes.
2. **Seed** state from the scenario's per-scenario data — a fake calendar, an in-memory database —
   that the agent's real tools read through unchanged.
3. **Mock tools for the session's lifetime**, so tool selection is still under test but execution
   is deterministic.
4. **Grade the final state** in the end-of-simulation callback: compare what the agent ended with
   against what the scenario expected, and fail the run if they diverge. Your check can only fail a
   run the judge passed — it can never rescue one the judge failed.

Only tool-flow scenarios need this; open-ended and adversarial ones are graded on the conversation
alone. The full treatment, including how to verify the wiring actually took effect, is in
`references/connecting-the-agent.md`. Look up the current API names with `reading-livekit-docs`.

## Grow the suite from real failures

The scenarios worth most describe something that actually went wrong. Once the agent is live, derive
them from recorded sessions rather than inventing more: where the CLI supports it, a subcommand
derives a scenario from a recorded session (check `lk agent simulate --help`). A derived
scenario describes one call — widen it into the class of calls it represents, and sharpen its
expectation into the rule you want enforced.

Every production bug you fix belongs in the file permanently.

## Don't write bad tests

The judge grades the agent against `agent_expectations`, so a careless expectation punishes correct
behavior:

- For guardrails and negative cases, the pass is that the agent **refuses, escalates, or declines to
  invent data**. Write it that way.
- Never write an expectation only reachable by misbehaving — stating data the agent can't know,
  giving specific medical, legal or financial directives. If passing requires misbehavior, the
  scenario is wrong.
- Judge by outcome, from the user's perspective. Never prescribe wording.

## References

- `references/risk-coverage.md` — turning constraints into a checklist and guaranteeing coverage
- `references/scenario-craft.md` — instructions shapes, persona variety, audio-specific scenarios
- `references/connecting-the-agent.md` — the agent-side code: detect, seed, mock, grade final state

## Related skills

- Running them: `running-livekit-simulations`
- Schema and CLI facts: `reading-livekit-docs`
