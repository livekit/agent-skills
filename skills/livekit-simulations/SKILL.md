---
name: livekit-simulations
description: 'DEPRECATED — do not use. This skill has been split into focused replacements. Superseded: use writing-livekit-scenarios to create and organize simulation scenarios and wire the agent to consume them, and running-livekit-simulations to run them and act on results.'
license: MIT
metadata:
  author: livekit
  version: "1.0.0"
---

# Deprecated

This skill has been replaced by focused skills. Load the one that matches the task:

| Task | Skill |
|---|---|
| Creating, refining and organizing scenarios; seeding state and grading final state | `writing-livekit-scenarios` |
| Running simulations, CI, triaging failures | `running-livekit-simulations` |

Do not follow this file's previous guidance. It described a pre-June-2026 command surface and
scenario schema: `lk agent simulate` now requires a `text` or `audio` subcommand, and scenario files
use `name` / `tags` / `userdata` rather than `agent_description` / `metadata`. Its bundled
`build_scenarios.py` emitted the superseded schema and has been removed.
