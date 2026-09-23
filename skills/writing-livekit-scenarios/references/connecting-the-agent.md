# Connecting scenarios to the agent

## Contents
- Detect the simulation, change nothing else
- Seed state from per-scenario data
- Mock tools for the session's lifetime
- Grade the final state, not just the transcript
- Which scenarios need this
- Check it actually took effect

Two problems make simulation suites untrustworthy, and both are fixed in the agent's code rather
than in the scenario file:

1. **Nondeterminism.** A scenario that reaches the real backend grades differently every run, and
   goes stale as that backend's data changes.
2. **A judge that only reads the conversation.** A polished, confident conversation can still have
   booked the wrong room. If the only verdict is the transcript's, that run passes.

Look up the current API names with `reading-livekit-docs` before writing any of this — the docs'
section on connecting scenarios to your agent has working code in each language. What follows is
the shape, which is stable; the names are not, and this reference deliberately doesn't restate them.

## Detect the simulation, change nothing else

The agent asks the job context whether it's running under a simulation. Under one it gets a
simulation context carrying the scenario and its per-scenario data; in production it gets nothing
back. That single branch is the whole integration:

- **Under simulation** — build state from the scenario's data and install mocks.
- **Otherwise** — connect to the real backends exactly as before.

Keep the branch at the top of the entrypoint, right after connecting. The context is available from
dispatch, so it's ready as soon as the entrypoint runs.

**The production path must stay untouched.** If wiring simulations changes how the agent behaves in
a real session, the simulation is no longer testing the thing you ship. One branch, one direction.

## Seed state from per-scenario data

Each scenario can carry an arbitrary nested mapping (the docs call it userdata) that is handed to
the agent at runtime. It's how one scenario says "these are the rooms free that day" and the next
says "nothing is free".

- **Keys arrive exactly as written** in the scenario file. Read them under the same names; don't
  expect a case conversion.
- **Seed the backend, don't special-case the agent.** Build a fake calendar, an in-memory database,
  a fixture inventory — something the agent's real tools read through unchanged. The moment the
  agent's *logic* branches on simulation state, the test stops testing the agent.
- **Pin the clock.** Scenarios written against absolute dates need the agent's notion of "now" fixed,
  usually from an environment variable, and optionally overridden per scenario. Without this, a
  suite silently rots as the calendar moves.

## Mock tools for the session's lifetime

A simulation runs a whole session on its own — nothing wraps the turns the way a test does. So mocks
must be installed for the session's lifetime rather than scoped to a block; the tool-mocking helper
has a form for exactly this case.

The model still sees the real tool schemas; only execution is intercepted. Tool *selection* stays
under test, which is usually the thing you most want graded.

Where a language has no session-scoped mocking helper, get the same result by defining tools inside
the entrypoint so they close over the state you seeded. Same principle: real schemas, seeded data.

## Grade the final state, not just the transcript

Register the end-of-simulation callback and compare the agent's final state against what the
scenario said should happen — conventionally an expected-state block in the scenario's data. If they
diverge, fail the run with a reason.

The semantics are worth being precise about, because they surprise people:

- **Your check can only fail a run.** The result is the AND of the judge's verdict and yours. You can
  fail a run the judge passed; you cannot rescue one the judge failed.
- **Doing nothing is valid.** If you don't fail it, the judge's verdict stands. Scenarios with no
  expected state should return early and be graded on the conversation alone.
- **The judge's verdict is readable** inside the callback, if you want to log it or make your check
  conditional on it.

Compare at the granularity you actually care about — room *type*, booking *status*, followup *kind*.
Asserting on every field of a record produces failures about formatting rather than behavior.

This is what turns a simulation into an evaluation: the run passes only if the conversation was right
*and* the agent ended in the right state.

## Which scenarios need this

Not all of them, and the split is a good reason to keep separate scenario files:

- **Tool-flow scenarios** driving a concrete outcome — these want seeded state and final-state
  grading. They're also the ones worth writing in point-form direction so the path is stable.
- **Open-ended and adversarial scenarios** — graded on the conversation alone. Seeding them adds
  nothing; most need no per-scenario data at all.

## Check it actually took effect

A silent failure here is expensive: the run looks fine while the agent talks to production data, or
a key is misspelled and the fake backend comes up empty.

Before trusting a suite, verify once that a seeded scenario really used the seeded state — run it
with `debugging-livekit-agents` or read a run's transcript and confirm the agent offered what you
seeded and not what the real backend holds. Then confirm that a deliberately wrong expected state
actually fails the run. A state check that never fails isn't a check.
