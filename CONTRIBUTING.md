# Contributing to LiveKit Agent Skills

Thanks for your interest in contributing! This project provides reusable skills that help AI coding agents build voice AI applications with LiveKit.

## How to Contribute

### Improving Existing Skills

The most valuable contributions improve skill content — making guidance clearer, fixing incorrect behavioral advice, or adding missing patterns that agents commonly need.

1. Fork and clone the repository
2. Create a branch from `main`
3. Make your changes
4. Open a pull request

### Adding a New Skill

New skills should follow the structure in `skills/livekit-agents/` as a reference:

```
skills/
└── your-skill-name/
    ├── SKILL.md          # The skill content
    └── references/       # Supporting documentation
```

Every skill must include YAML frontmatter:

```yaml
---
name: skill-name-kebab-case
description: >-
  Trigger phrases and brief description that help agents
  recognize when to activate this skill.
license: MIT
metadata:
  author: your-name
  version: "0.1.0"
---
```

### Filing Issues

- **Bug reports**: Skill content that causes agents to produce incorrect code or behavior
- **Skill requests**: Ideas for new skills that would help agents build with LiveKit
- **Questions**: General questions about usage or design

## Skill Content Principles

All contributions must follow the **"freeze forever" principle** — content should remain correct indefinitely without updates.

### Encode behavior, not knowledge

Skills teach *how to approach* problems, not API specifics. API signatures, configuration options, and method names change — behavioral guidance does not.

**Good**: "Always test agent implementations by verifying audio pipeline connectivity"
**Bad**: `session = AgentSession(llm=openai.LLM(model="gpt-4o"))`

### Direct to MCP for facts

All factual information must come from the [LiveKit Docs MCP server](https://docs.livekit.io/mcp). Skills should instruct agents to look up current API details rather than hardcoding them.

### Require testing

Every skill that guides agent implementation must include testing expectations. Agents should never produce untested code.

### Stay under 500 lines

Skills are loaded into agent context windows. Keep them concise — under 500 lines — so they don't crowd out the user's actual project context.

## File Naming Conventions

- Skill directories use `kebab-case`
- `SKILL.md` is the only uppercase filename in a skill directory
- Supporting documents go in `references/`

## Development Setup

These skills are designed to work with the LiveKit Docs MCP server. To test MCP integration locally, install the server following the instructions at:

https://docs.livekit.io/mcp

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
