# LiveKit Agent Skills

Skills that teach AI coding agents (Claude Code, Cursor, Codex, and anything else that reads the
[Agent Skills](https://agentskills.io) format) how to build, test, and ship voice AI agents with
[LiveKit](https://livekit.io).

Without these skills, a coding agent working on a LiveKit project guesses at APIs from stale
training data, ships prompt changes it never tried, and doesn't know the LiveKit tooling exists.
With them, it looks facts up before writing code, live-tests changes in a conversation, writes
turn-level tests, and runs simulations before a release.

## What you get

Six skills, one per job in the development loop. Each is small and hands off to the others by
name, so a task typically loads two or three of them instead of one large document.

| Stage | Skill | What it does |
|---|---|---|
| Know | **reading-livekit-docs** | Looks up current LiveKit facts (APIs, CLI flags, changelogs, pricing) through the Docs MCP server or `lk docs` instead of answering from memory. The other skills load it first. |
| Build | **building-livekit-agents** | Architecture for low-latency voice agents: keeping context small, splitting monoliths into handoffs and tasks, designing for users who listen rather than read. |
| Try | **debugging-livekit-agents** | Drives a multi-turn conversation with the agent running locally in text mode, via `lk agent debugger`, and reads the tool calls behind each reply. The default way to check a change. |
| Test | **testing-livekit-agents** | Turn-level tests in the project's own pytest or Vitest suite: assertions on messages, tool calls and handoffs, LLM judging of intent, tool mocking. |
| Simulate | **writing-livekit-scenarios** | Creates the scenarios a simulation runs (generate a baseline, refine it, cover the hard cases, organize into sets) and wires the agent to seed state from them and grade its final state. |
| Ship | **running-livekit-simulations** | Runs simulations in text or audio mode, against a local or deployed agent, in CI before a release, and triages the failures. |

You don't invoke skills by name. Your coding agent picks them up from what you say:

- *"does livekit support gemini realtime?"* · *"what changed in agents 1.8?"* → reading
- *"add a tool that looks up an order"* · *"this agent feels sluggish, restructure it"* → building
- *"test my agent"* · *"try it as a confused first-time caller"* · *"why did it call that tool?"* → debugging
- *"write pytest tests for the greeting"* · *"pin that bug as a test"* → testing
- *"what should I test before we ship?"* · *"my simulations are flaky"* → writing scenarios
- *"run the scenarios and tell me what failed"* · *"test barge-in in audio mode"* → running

## Install

```bash
npx skills add livekit/agent-skills
```

That installs all six for whichever coding agents you use. You can also copy the folders you want
from `skills/` into your agent's skills directory (for Claude Code, `.claude/skills/` in your
project).

You'll also want:

- **The LiveKit CLI (`lk`).** Three skills drive it: `lk docs`, `lk agent debugger`, and
  `lk agent simulate`. Install or update it from the [CLI docs](https://docs.livekit.io/intro/basics/cli).
  The skills check for the commands they need and will tell you to update if one is missing.
- **A LiveKit Cloud project**, with `lk` authenticated to it, for simulations.
- **The LiveKit Docs MCP server** (optional). It's the same source `lk docs` uses, with less
  friction. Setup for each coding agent is at
  [docs.livekit.io/intro/mcp-server](https://docs.livekit.io/intro/mcp-server/).

## How the skills are built

The skills are conceptual. They teach how to approach a job (what to check, what goes wrong, which
tool fits) and send the agent to `--help` and the live docs for flags, schemas, and API names. That
keeps them correct as LiveKit changes. "Start the agent, send turns, read the tool calls, restart
after an edit" stays the same even when the flag list changes.

So expect your agent to look things up while using them. That's intended.

The design rules, authoring conventions, and the eval harness that checks each skill triggers on
the right requests are in [AGENTS.md](AGENTS.md).

## Deprecated skills

`livekit-agents` and `livekit-simulations` were split into the six skills above. Their directories
remain as stubs whose descriptions point at the replacements. If your agent still has them
installed, reinstall to pick up the new set.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the process and [AGENTS.md](AGENTS.md) for how skills
here are written and evaluated. The most useful bug reports are about skill content: an agent
followed a skill and did the wrong thing.

## License

MIT
