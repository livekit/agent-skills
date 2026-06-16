# AGENTS.md

This repository contains AI agent skills for building with LiveKit. The skills follow the [Agent Skills](https://agentskills.io) format.

## Repository Structure

```
agent-skills/
├── README.md           # User-facing documentation
├── AGENTS.md           # This file (for AI agents)
├── CLAUDE.md           # Points to AGENTS.md
└── skills/
    ├── livekit-agents/         # LiveKit Agents skill
    │   ├── SKILL.md            # The skill content
    │   └── references/         # Supporting documentation
    └── livekit-simulations/    # LiveKit Simulations skill
        ├── SKILL.md            # The skill content
        ├── references/         # Supporting documentation
        └── scripts/            # Supporting scripts
```

## Contributing Guidelines

### Skill Content Principles

All skills in this repository must follow the "freeze forever" principle:

1. **Encode behavior, not knowledge** - Skills teach *how to approach* problems, not API specifics
2. **Direct to MCP for facts** - All factual information must come from live documentation
3. **Require testing** - Every agent implementation must include tests
4. **Stay under 500 lines** - Keep skills concise for context efficiency

### SKILL.md Format

Each skill requires YAML frontmatter:

```yaml
---
name: skill-name-kebab-case
description: Trigger phrases and brief description. Include phrases like "build a voice agent" that help agents recognize when to use this skill.
license: MIT
metadata:
  author: livekit
  version: "X.Y.Z"
---
```

### File Naming

- Skill directories use `kebab-case`
- `SKILL.md` is the only uppercase filename
- Supporting docs go in `references/` subdirectory

## LiveKit MCP Server

These skills are designed to work with the LiveKit Docs MCP server. If you're working on this repository and need to test MCP integration, make sure it is installed. Installation instructions are available at https://docs.livekit.io/intro/mcp-server/


## Links

- [LiveKit Documentation](https://docs.livekit.io)
- [LiveKit Agents SDK](https://github.com/livekit/agents)
- [Agent Skills Format](https://agentskills.io)
