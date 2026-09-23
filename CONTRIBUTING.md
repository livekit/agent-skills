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

New skills should follow the structure of an existing one — `skills/writing-livekit-scenarios/` is the
fullest example. Before writing, read [AGENTS.md](AGENTS.md): it holds the authoring rules and the
evaluation harness, and a new skill is expected to arrive with eval results.

```
skills/
└── your-skill-name/
    ├── SKILL.md          # The skill content
    └── references/       # Supporting documentation
```

Every skill must include YAML frontmatter:

```yaml
---
name: doing-something-with-livekit        # gerund form, lowercase, hyphens
description: >-
  Third person: what the skill does, the phrases a user types
  for this job, and which sibling skill handles adjacent jobs.
license: MIT
metadata:
  author: livekit
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

**Good**: "Restart the debugger after every code edit — a running session holds the old code."
**Bad**: a list of the debugger's flags, a schema's field names, or `AgentSession(llm=openai.LLM(model="gpt-4o"))`

### Direct to MCP for facts

All factual information must come from live sources — `--help` on the installed CLI, `lk docs`, or the
[LiveKit Docs MCP server](https://docs.livekit.io/intro/mcp-server/). Skills stay conceptual and instruct
agents to look up current API details rather than hardcoding them.

### Require testing

Skills that guide building an agent must send the agent on to verify its work (`debugging-livekit-agents`,
`testing-livekit-agents`). Agents should never hand back untested code.

### Stay under 500 lines

Skills are loaded into agent context windows. Keep them concise — under 500 lines — so they don't crowd out the user's actual project context.

## File Naming Conventions

- Skill directories are gerund-form `kebab-case`: `building-livekit-agents`, `running-livekit-simulations`
- `SKILL.md` is the only uppercase filename in a skill directory
- Supporting documents go in `references/`, one level deep, with a `## Contents` list when over 100 lines

## Development Setup

You'll want the LiveKit CLI (`lk`) installed and, ideally, the Docs MCP server
(https://docs.livekit.io/intro/mcp-server/), since several skills drive them.

To check your change, run `python3 evals/validate.py`, and if you touched a `description`, the trigger
eval in `evals/trigger/`. Both are described in [AGENTS.md](AGENTS.md#evaluating-skills).

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
