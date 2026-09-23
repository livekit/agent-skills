---
name: livekit-agents
description: 'DEPRECATED — do not use. Split into focused skills: building-livekit-agents for agent architecture, reading-livekit-docs for API facts and documentation lookup, testing-livekit-agents for turn-level tests, and debugging-livekit-agents to live-test an agent during development.'
license: MIT
metadata:
  author: livekit
  version: "1.0.0"
---

# Deprecated

This skill has been replaced by focused skills. Load the one that matches the task:

| Task | Skill |
|---|---|
| Building an agent; architecture, handoffs, latency | `building-livekit-agents` |
| Looking up APIs, CLI flags, changelogs, pricing | `reading-livekit-docs` |
| Live-testing an agent while developing it | `debugging-livekit-agents` |
| Turn-level tests in pytest or Vitest | `testing-livekit-agents` |

Don't follow this file's previous guidance. The file is kept only so existing references still resolve.
