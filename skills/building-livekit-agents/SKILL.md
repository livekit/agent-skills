---
name: building-livekit-agents
description: 'Builds voice and chat AI agents with LiveKit Agents and LiveKit Cloud. Use when the user asks to "build a voice agent", "create a LiveKit agent", "add voice AI to my app", "implement handoffs", "structure an agent workflow", "my agent is slow / too chatty", or is writing code against the LiveKit Agents SDK. Covers architecture: latency-first design, keeping context small, splitting monolithic agents into handoffs and tasks, and voice-specific interaction design. For API specifics use reading-livekit-docs; for verifying behavior use debugging-livekit-agents and testing-livekit-agents.'
license: MIT
metadata:
  author: livekit
  version: "1.0.0"
---

# Building LiveKit agents

This skill is about *how to think* about a voice agent's structure. It deliberately contains
no API specifics — those change, and they come from `reading-livekit-docs`.

It assumes LiveKit Cloud, which is the recommended path: managed infrastructure, and
**LiveKit Inference** for models so there are no per-provider API keys to manage. If the user
is self-hosting, the architecture below still holds; the Inference guidance does not.

## Before you write code

1. **Load `reading-livekit-docs`** and look up the APIs you're about to use. Never write LiveKit
   code from memory.
2. **Confirm the project is connected to a LiveKit Cloud project** — `LIVEKIT_URL`,
   `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, usually in `.env`. The CLI can set these up.
3. **Decide the workflow shape before the first agent class**, per "Structure" below. Retrofitting
   a monolith into handoffs is much more work than starting with two agents.
4. **Plan how you will verify it.** Not "I'll test at the end" — decide now which of
   `debugging-livekit-agents` (drive a real conversation) and `testing-livekit-agents` (assert on turns)
   you'll use, because it changes how you factor the code.

## Voice changes the requirements

A voice agent is not a chat agent with a speaker attached. Three constraints drive nearly every
design decision:

**Latency is a feature.** Users expect a reply in hundreds of milliseconds. Every architectural
choice either spends or saves that budget: context size, tool count, whether a tool call sits on
the critical path, whether responses stream. Design for the unhappy path too — network stalls and
provider timeouts are normal, not exceptional.

**Context bloat is latency.** A 10,000-token system prompt with 50 tool definitions feels sluggish
no matter which model is behind it, because the model re-reads all of it every turn. Carry the
minimum: only the tools reachable from the current phase, only the instructions that phase needs.

**Users listen, they don't read.** They can't skim, can't scroll back, and will talk over the
agent. Long replies are a bug. Silence reads as broken. Interruption is the normal case, not the
edge case.

## Structure: handoffs and tasks

The default failure mode is one agent that does everything. It accumulates every tool, every
instruction, and every piece of state until it is both slow and unreliable — and by then splitting
it is a rewrite.

**Handoffs** transfer control from one agent to another. Use them at natural conversation
boundaries — greeting → intake → resolution, or general support → billing specialist. The win is
that each agent carries only its own tools and instructions. Design the boundary where the context
can be *summarized* rather than handed over wholesale; if the next agent needs everything the
previous one had, the boundary is in the wrong place.

**Tasks** are tightly scoped prompts aimed at one outcome. Use them for discrete operations that
don't need a full agent, or where a focused prompt beats a general-purpose one.

A useful check: if you can't state in one sentence what an agent is responsible for, it should be
more than one agent.

## Tools

- **Tool descriptions are behavior.** When an agent calls the wrong tool, or calls one at the wrong
  time, suspect the description before the model. A description that doesn't say *when* to use the
  tool is the single most common cause.
- **Keep tools off the critical path where you can.** A tool call the user waits through is latency
  they hear.
- **Design for failure at the tool boundary.** Decide what the agent says when a backend is down or
  returns nothing — an agent that invents an answer under tool failure is the hardest bug to catch
  later.

## Verify before you call it done

Agent behavior is code, and prompt changes break it as thoroughly as code changes do. "It seemed
fine when I tried it" is not verification.

- **While building**, drive real conversations with `debugging-livekit-agents` — it runs your agent
  locally in text mode and lets you send turns and read the tool calls behind each reply.
- **Before you call it done**, write tests with `testing-livekit-agents`. At minimum: the core
  behavior the user asked for, tool invocation with correct arguments if tools exist, and one
  unhappy path.
- **Before shipping a change to a live agent**, run simulations — `writing-livekit-scenarios` and
  `running-livekit-simulations`.

If the user explicitly asks for no tests, build without them, say once that you'd recommend them
before production, and move on.

## Common mistakes

- **Starting monolithic "just for now."** The structure is what you're deciding; the implementation
  can be simple.
- **Treating latency as a later problem.** It compounds, and it never gets cheaper to fix.
- **Copying an example without understanding it.** Examples demonstrate one pattern; pasted whole
  they bring context bloat and components you can't explain.
- **Assuming your model knowledge is current.** It isn't. See `reading-livekit-docs`.
- **Shipping on manual testing alone.** Prompt edits silently change behavior; tests are how you
  find out before users do.

## Related skills

- Facts, APIs, changelogs: `reading-livekit-docs`
- Drive a live conversation while building: `debugging-livekit-agents`
- Turn-level tests: `testing-livekit-agents`
- Whole-conversation testing: `writing-livekit-scenarios`, `running-livekit-simulations`
