# AGENTS.md

This repository contains AI agent skills for building with LiveKit. The skills follow the [Agent Skills](https://skills.sh) format.

## Repository Structure

```
agent-skills/
├── README.md           # User-facing documentation
├── AGENTS.md           # This file (for AI agents)
├── CLAUDE.md           # Points to AGENTS.md
└── skills/
    └── SKILL.md        # The skill content
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

### Testing Changes

Before submitting changes to skills:

1. Test with the eval harness at `github.com/livekit-examples/agent-evals`
2. Verify the skill triggers correctly for intended prompts
3. Confirm MCP integration works when available
4. Check that agents write tests when using the skill

### File Naming

- Skill directories use `kebab-case`
- `SKILL.md` is the only uppercase filename
- Scripts (if any) go in `scripts/` subdirectory

## LiveKit MCP Server

These skills are designed to work with the LiveKit Docs MCP server. If you're working on this repository and need to test MCP integration, make sure it is installed.  Installation commands can be found in @README.md for your agent of choice.


## Links

- [LiveKit Documentation](https://docs.livekit.io)
- [LiveKit Agents SDK](https://github.com/livekit/agents)
- [Agent Skills Format](https://skills.sh)
