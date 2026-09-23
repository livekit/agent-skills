---
name: testing-livekit-agents
description: 'Writes turn-level tests for a LiveKit agent in the user''s normal test suite — pytest (Python) or Vitest (Node.js). Use when the user asks to "write tests for my agent", "add a test for this tool", "test the handoff", "pin this bug", "why does my agent test fail", or after building or changing agent behavior that needs regression coverage. Covers the AgentSession test harness, event assertions on messages, tool calls and handoffs, LLM-based `judge()` on intent, mocking tools, multi-turn tests, and whole-conversation judging with JudgeGroup. For interactive poking use debugging-livekit-agents; for whole-conversation grading at scale use running-livekit-simulations.'
license: MIT
metadata:
  author: livekit
  version: "1.0.0"
---

# Testing LiveKit agents

Turn-level tests are the cheapest real verification an agent can have: they run in the user's
existing suite, in text mode, fast enough for every commit. The framework's helper names and
signatures move — look them up with `reading-livekit-docs` before writing, and treat the testing
docs page as the source for every API detail this skill leaves out.

The shape is always the same: start a test session with the agent under test, run one user turn,
and assert on the sequence of events that turn produced.

## What a test asserts on

A turn is a *sequence of events*, not just a reply. A simple turn is one message; a real one is a
tool call, its output, maybe a handoff, then a message. Tests are built by walking that sequence
in order and asserting on each event, then asserting the turn contains nothing more.

Three kinds of assertion, and knowing which to reach for is most of the skill:

**Structural** — message roles, that a tool was called, with which arguments, what it returned,
that a handoff to a specific agent happened. Deterministic. Prefer these: they fail for exactly
one reason.

**Judged** — an LLM-judge helper hands one message plus an intent string to a model and asks
whether it matches. Use it for the *content* of a reply, which you can't assert exactly. Describe the intent
by outcome ("tells the user the booking is confirmed and gives the time"), never by wording.

**Whole-conversation** — a judge-group helper runs several built-in judges concurrently over the
whole chat history and aggregates the verdicts. The built-in judges cover the usual dimensions —
grounding, relevance, safety, task completion, tool use, and more; the docs list the current set.
Reach for this when the question spans turns rather than sitting in one.

Rules of thumb:

- **Assert structure first, judge only what's left.** A judged assertion that could have been a
  structural one is a slower, flakier version of the same test.
- **Close the turn.** Assert there are no further events, or a test passes while the agent also
  does something you never intended.
- **One behavior per test.** A test that asserts six things tells you almost nothing when it fails.

## Mocking tools

Tests should not hit real backends — that's how a suite becomes slow and nondeterministic. Override
the tools for the agent under test and return fixed values.

Two things worth knowing beyond the API:

- **Mock the failure, not just the success.** Returning an error from a mock makes the tool raise,
  which is how you test what the agent *says* when a backend is down. This is the highest-value
  test most agents don't have, and the behavior users notice most.
- **Scope matters.** The default scoping is a block around your own `run()` calls, which is what a
  test wants. There is also a session-scoped form for when a session runs on its own and needs
  mocks active for its lifetime — that's what a simulation entrypoint uses, not a test. See
  `writing-livekit-scenarios`.

Mocking changes only execution: the model still sees the real tool schemas, so tool *selection* is
still genuinely under test.

## Multi-turn and seeded history

Two ways to test behavior that depends on what came before:

- **Run the turns.** Successive turns build real conversation history, so the second turn sees
  the first. Use this when the path matters — collecting details across turns, changing mind
  mid-flow, a handoff carrying context.
- **Seed the history.** Construct a chat history and hand it to the agent to jump straight to the
  interesting state. Use this when the setup turns aren't what you're testing; it's faster and less
  brittle than replaying five turns to reach turn six.

## What to test

Cover, in roughly this order of value:

1. **The behavior the user asked for.** Every agent gets at least this.
2. **Tool invocation** — right tool, right arguments, for a representative request.
3. **Tool failure** — what the agent says when a tool errors or returns nothing.
4. **Refusals and limits** — that the agent declines what it should decline, and doesn't invent
   data it can't have. The pass condition is the refusal.
5. **Handoffs** — that the transition fires when it should, and the next agent still has what it
   needs.
6. **Every bug you've fixed.** A fixed bug without a test is a bug waiting to come back.

## Don't write tests that punish correct behavior

The most common bad agent test asserts the agent does something it *shouldn't*: states data it
can't know, gives a specific medical/legal/financial recommendation, completes a flow that should
have been blocked. If the only way to pass is to misbehave, the test is wrong — fix the test.

For a guardrail, the pass is that the agent refuses, escalates, or declines to invent. Write the
assertion that way.

## Where this sits

- **Interactive poking while building** → `debugging-livekit-agents`. Faster loop, no assertions kept.
- **Turn-level, deterministic, every commit** → here. Cheapest lasting check.
- **Whole conversations graded by a simulated user, before a release** → `running-livekit-simulations`.
  More expensive; catches emergent behavior these can't.

When a simulation keeps failing the same way, the bug is usually turn-level. Move it down here: it
pins the cause more precisely and catches it earlier.

## Related skills

- Current API surface: `reading-livekit-docs`
- Finding the bug first: `debugging-livekit-agents`
- Simulations, including seeded state and session-scoped mocks: `writing-livekit-scenarios`, `running-livekit-simulations`
