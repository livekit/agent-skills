# LiveKit Agent Skills

Skills that teach AI coding agents (Claude Code, Cursor, Codex, Gemini CLI, and anything else that
reads the [Agent Skills](https://agentskills.io) format) how to build, test, and ship voice agents
with [LiveKit](https://livekit.io) and the LiveKit Agents SDK for Python and Node.js. Includes a
Claude Code plugin that bundles the skills with the LiveKit Docs MCP server.

Without these skills, a coding agent working on a LiveKit project guesses at APIs from stale
training data, ships prompt changes it never tried, and doesn't know the LiveKit tooling exists.
With them, it looks facts up before writing code, live-tests changes in a conversation, writes
turn-level tests, and runs simulations before a release.

## What you get

Seven skills, one per job in the development loop. Each is small and hands off to the others by
name, so a task typically loads two or three of them instead of one large document.

| Stage | Skill | What it does |
|---|---|---|
| Know | **reading-livekit-docs** | Looks up current LiveKit facts (APIs, CLI flags, changelogs, pricing) through the Docs MCP server or `lk docs` instead of answering from memory. The other skills load it first. |
| Build | **building-livekit-agents** | Architecture for low-latency voice agents: keeping context small, splitting monoliths into handoffs and tasks, designing for users who listen rather than read. |
| Try | **debugging-livekit-agents** | Drives a multi-turn conversation with the agent running locally in text mode, via `lk agent debugger`, and reads the tool calls behind each reply. The default way to check a change. |
| Test | **testing-livekit-agents** | Turn-level tests in the project's own pytest or Vitest suite: assertions on messages, tool calls and handoffs, LLM judging of intent, tool mocking. |
| Simulate | **writing-livekit-scenarios** | Creates the scenarios a simulation runs (generate a baseline, refine it, cover the hard cases, organize into sets) and wires the agent to seed state from them and grade its final state. |
| Ship | **running-livekit-simulations** | Runs simulations in text or audio mode, against a local or deployed agent, in CI before a release, and triages the failures. |
| Operate | **operating-livekit-agents** | Deploys a version to LiveKit Cloud and rolls it back, and keeps a live agent healthy: the worker process model and prewarming, safe async in workers, provider timeouts, graceful shutdown, SDK upgrades, observability, and changing a codebase that's already in production. |

You don't invoke skills by name. Your coding agent picks them up from what you say:

- *"does livekit support gemini realtime?"* · *"what changed in agents 1.8?"* → reading
- *"add a tool that looks up an order"* · *"this agent feels sluggish, restructure it"* → building
- *"test my agent"* · *"try it as a confused first-time caller"* · *"why did it call that tool?"* → debugging
- *"write pytest tests for the greeting"* · *"pin that bug as a test"* → testing
- *"what should I test before we ship?"* · *"my simulations are flaky"* → writing scenarios
- *"run the scenarios and tell me what failed"* · *"test barge-in in audio mode"* → running
- *"deploy my agent"* · *"roll back to yesterday's version"* · *"first call after a restart is slow"* → operating

## Install

### LiveKit CLI

```bash
lk skills install
```

That installs all seven skills for every coding agent it finds on your machine (Claude Code,
Codex, Cursor, GitHub Copilot, Gemini CLI, and others), and adds the LiveKit Docs MCP server to
each one's config. `lk skills update` pulls the latest; `lk skills --help` has the rest.
`lk agent init` offers to do this for new agent projects.

### Claude Code

Install the LiveKit plugin. It bundles all seven skills and the LiveKit Docs MCP server, and Claude
Code keeps it up to date in the background.

```
/plugin marketplace add livekit/agent-skills
/plugin install livekit@livekit
```

Plugin skills are namespaced, so if you invoke one by hand it's `/livekit:building-livekit-agents`
rather than `/building-livekit-agents`. You rarely need to: Claude picks them up from what you say.

### npx skills

```bash
npx skills add livekit/agent-skills
```

That installs all seven for whichever coding agents you use. `npx skills add https://livekit.com`
works too.

You can also copy the folders you want from `skills/` into your agent's skills directory.

### You'll also want

- **The LiveKit CLI (`lk`).** Four skills drive it: `lk docs`, `lk agent debugger`,
  `lk agent simulate`, and the `lk agent` deploy commands. Install or update it from the [CLI docs](https://docs.livekit.io/intro/basics/cli).
  The skills check for the commands they need and will tell you to update if one is missing.
- **A LiveKit Cloud project**, with `lk` authenticated to it, for simulations and deployment.
- **The LiveKit Docs MCP server** (optional, and already included in the Claude Code plugin). It's
  the same source `lk docs` uses, with less friction. Setup for each coding agent is at
  [docs.livekit.io/intro/mcp-server](https://docs.livekit.io/intro/mcp-server/).

## How the skills are built

The skills are conceptual. They teach how to approach a job (what to check, what goes wrong, which
tool fits) and send the agent to `--help` and the live docs for flags, schemas, and API names. That
keeps them correct as LiveKit changes. "Start the agent, send turns, read the tool calls, restart
after an edit" stays the same even when the flag list changes.

So expect your agent to look things up while using them. That's intended.

The design rules, authoring conventions, and the eval harness that checks each skill triggers on
the right requests are in [AGENTS.md](AGENTS.md).

## Upgrading from the old skills

`livekit-agents` and `livekit-simulations` were split into the seven skills above and removed. If
your agent still has either installed, delete it and reinstall with one of the methods under
[Install](#install).

A stale copy of `livekit-simulations` in particular will steer an agent wrong — it described a CLI
surface that no longer exists.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the process and [AGENTS.md](AGENTS.md) for how skills
here are written and evaluated. The most useful bug reports are about skill content: an agent
followed a skill and did the wrong thing.

## License

MIT
