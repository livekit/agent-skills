---
name: debugging-livekit-agents
description: 'Drives a real multi-turn conversation with a LiveKit agent running locally, to see what it actually does. Use when the user says "test my agent", "try my agent", "does this work", "why did it call that tool", "it says the wrong thing when I ask X", "test this change", or whenever you have edited an agent and need to verify the behavior rather than guess. Wraps `lk agent debugger`: start the agent in text mode, send turns, read the tool calls, handoffs, errors and logs behind each reply, then restart after an edit. This is the preferred way for a coding agent to live-test during development — no audio, no LiveKit room, one LLM call per turn — and the default when the user says "test" without naming unit tests or simulations.'
license: MIT
metadata:
  author: livekit
  version: "1.0.0"
---

# Debugging a LiveKit agent live

`lk agent debugger` runs the user's agent locally as a background process in text mode and lets
you drive a conversation one turn at a time. It exists for coding agents: you stand in for the
user, decide the next line from the last reply, and inspect what the agent did in between.

Speech is disabled and nothing is sent to a LiveKit room, so a turn costs only the agent's own
LLM and tool calls. That makes it cheap enough to use constantly while building.

**Confirm the command exists and read its help before the first use:**

```bash
lk agent debugger --help
```

The help is thorough and is the source of truth for subcommands and flags — this skill
deliberately doesn't restate them. If the command is missing, the installed CLI predates it: tell
the user to update `lk`, and fall back to `testing-livekit-agents` meanwhile. Don't guess at an
older command's shape.

## The loop

The shape is: **start** the agent → **say** user turns → **inspect** what happened → edit the code
→ **restart** → repeat → **stop**. Roughly:

```bash
lk agent debugger start
lk agent debugger say "Hi, what can you do?"
lk agent debugger say "Book me a table for two tonight"
lk agent debugger stop
```

Each `say` prints everything the agent did in response — tool calls with their arguments and
results, handoffs, errors — and then the reply. Between turns there are subcommands for the
agent's own chat history, a live event stream, the process logs, and status; `--help` lists them.

**Restart after every code edit.** A running session holds the old code. This is the mistake that
costs the most time: debugging behavior the file no longer has.

## How to actually debug with it

**Read the tool calls, not just the reply.** The reply tells you *what* went wrong; the tool call
with its arguments tells you *why*. A wrong argument is a prompt or tool-description bug; no call at
all is usually a tool description that never says when to use it.

**Interleave the logs when a tool misbehaves.** There's an option to show the agent's log lines
under the turn they belong to, which puts a tool's traceback directly beneath the sanitized error
the user would have heard — the fastest route from symptom to cause.

**Trust the agent's own chat history over your memory of the conversation.** It's the record of
what the LLM actually saw, including instruction and tool changes across handoffs. When behavior
seems impossible, the history usually shows the context isn't what you assumed.

**Reproduce before you fix, and re-run the same turns after.** Keep the sequence of `say` lines
that triggered the bug; it's your before/after.

**Drive conversations, not single turns.** Most real bugs are multi-turn: information collected
early that doesn't survive, a change of mind mid-flow, a handoff that drops context. One turn can't
find those.

**Script it when you're deciding programmatically.** There's machine-readable output and
meaningful exit codes for a program driving the loop; check `--help` for the current shape rather
than assuming a field name.

## When to use something else

| Situation | Use |
|---|---|
| You want to *hear* it, or hand the user something to try | `lk agent console` (mic and speakers, a human at the keyboard) |
| The same failure keeps coming back | A turn-level regression test — `testing-livekit-agents` |
| You need whole-conversation outcomes graded at scale | Simulations — `running-livekit-simulations` |
| The bug is about speech: turn-taking, interruptions, transcription | Audio simulations — the debugger is text-only and cannot see these |

The debugger is for *finding* a bug interactively. Once you've found one, move it down into a test
so it can't come back quietly — a bug you only ever caught by hand will return.

## Related skills

- Building the agent: `building-livekit-agents`
- Pinning a found bug as a test: `testing-livekit-agents`
- Whole-conversation checks: `writing-livekit-scenarios`, `running-livekit-simulations`
- CLI flags and API facts: `reading-livekit-docs`
