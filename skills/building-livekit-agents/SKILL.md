---
name: building-livekit-agents
description: 'Builds voice and chat AI agents with LiveKit Agents and LiveKit Cloud. Use when the user asks to "build a voice agent", "create a LiveKit agent", "add voice AI to my app", "implement handoffs", "structure an agent workflow", "my agent is slow / too chatty", or is writing code against the LiveKit Agents SDK. Covers architecture: designing for latency, keeping context small, splitting a monolithic agent into handoffs and tasks, and designing for voice. For API specifics use reading-livekit-docs. To check behavior use debugging-livekit-agents and testing-livekit-agents.'
license: MIT
metadata:
  author: livekit
  version: "1.0.0"
---

# Building LiveKit agents

This skill covers how to structure a voice agent. It has no API specifics, because those change;
get them from `reading-livekit-docs`.

It assumes LiveKit Cloud, the recommended path: managed infrastructure, plus **LiveKit Inference**
for models so you don't manage per-provider API keys. If the user is self-hosting, the
architecture advice still applies but the Inference guidance doesn't.

## Before you write code

1. **Load `reading-livekit-docs`** and look up the APIs you're about to use. Don't write LiveKit
   code from memory.
2. **Confirm the project is connected to a LiveKit Cloud project**: `LIVEKIT_URL`,
   `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, usually in `.env`. The CLI can set these up.
3. **Decide the workflow shape before writing the first agent class** (see "Structure" below).
   Splitting a monolith into handoffs later is much more work than starting with two agents.
4. **Plan how you'll verify it.** Decide now whether you'll use `debugging-livekit-agents` (drive a
   real conversation), `testing-livekit-agents` (assert on turns), or both, because it affects how
   you factor the code.

## How voice changes the requirements

A voice agent is more than a chat agent with a speaker attached. These constraints drive most
design decisions:

**Latency.** Users expect a reply within a few hundred milliseconds. Context size, tool count,
whether a tool call sits on the critical path, and whether responses stream all add to or save from
that budget. Plan for network stalls and provider timeouts too; they happen routinely.

**Context size.** A 10,000-token system prompt with 50 tool definitions feels sluggish on any
model, because the model re-reads all of it every turn. Give each phase only the tools it can reach
and the instructions it needs.

**Listening.** Users can't skim or scroll back, and they'll talk over the agent. Long replies are a
bug, silence sounds broken, and interruptions are normal.

## Structure: handoffs and tasks

The usual failure is one agent that does everything. It collects every tool, instruction, and piece
of state until it's slow and unreliable, and by that point splitting it is a rewrite.

**Handoffs** transfer control from one agent to another. Put them at natural conversation
boundaries, like greeting → intake → resolution, or general support → billing specialist. Each
agent then carries only its own tools and instructions. Choose a boundary where the context can be
summarized for the next agent. If the next agent needs everything the previous one had, the
boundary is in the wrong place.

**Tasks** are tightly scoped prompts aimed at one outcome. Use them for discrete operations that
don't need a full agent, or where a focused prompt works better than a general one.

If you can't say in one sentence what an agent is responsible for, split it.

## Tools

- **Tool descriptions drive behavior.** When an agent calls the wrong tool or calls one at the
  wrong time, check the description before blaming the model. The most common cause is a
  description that doesn't say when to use the tool.
- **Keep tools off the critical path where you can.** Users hear every tool call they wait on as
  latency.
- **Plan for tool failure.** Decide what the agent says when a backend is down or returns nothing.
  An agent that makes up an answer when a tool fails is very hard to catch later.

## Verify before you call it done

Prompt changes break agent behavior as easily as code changes do, and trying it once by hand
doesn't count as verification.

- **While building**, drive conversations with `debugging-livekit-agents`. It runs your agent
  locally in text mode, lets you send turns, and shows the tool calls behind each reply.
- **Before you call it done**, write tests with `testing-livekit-agents`. At minimum, cover the core
  behavior the user asked for, tool invocation with correct arguments if there are tools, and one
  failure path.
- **Before shipping a change to a live agent**, run simulations with `writing-livekit-scenarios`
  and `running-livekit-simulations`.

If the user asks for no tests, build without them, mention once that you'd recommend them before
production, and move on.

## Common mistakes

- **Starting with one agent "just for now."** You're deciding the structure up front; the
  implementation can still be simple.
- **Putting off latency.** It compounds, and it only gets more expensive to fix.
- **Copying an example you don't understand.** An example shows one pattern. Pasted whole, it brings
  extra context and components you can't explain.
- **Assuming your model knowledge is current.** It isn't. See `reading-livekit-docs`.
- **Shipping on manual testing alone.** Prompt edits change behavior without any visible error, and
  tests let you find out before users do.

## Related skills

- Facts, APIs, changelogs: `reading-livekit-docs`
- Drive a live conversation while building: `debugging-livekit-agents`
- Turn-level tests: `testing-livekit-agents`
- Whole-conversation testing: `writing-livekit-scenarios`, `running-livekit-simulations`
