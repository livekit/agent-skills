# Contributing to LiveKit Agent Skills

Thanks for contributing. This project provides reusable skills that help AI coding agents build voice AI applications with LiveKit.

## How to Contribute

### Improving Existing Skills

The most useful contributions improve skill content: clearer guidance, fixes to incorrect behavioral advice, or patterns agents commonly need that are missing.

1. Fork and clone the repository
2. Create a branch from `main`
3. Make your changes
4. Open a pull request

### Adding a New Skill

Follow the structure of an existing skill. `skills/writing-livekit-scenarios/` is the fullest
example. Read [AGENTS.md](AGENTS.md) before you start. It has the authoring rules and the eval
harness, and a new skill is expected to come with eval results.

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

All contributions follow the "freeze forever" principle: content should stay correct indefinitely without updates.

### Encode behavior, not knowledge

Skills teach how to approach problems, not API specifics. API signatures, configuration options, and method names change. Behavioral guidance doesn't.

**Good**: "Restart the debugger after every code edit — a running session holds the old code."
**Bad**: a list of the debugger's flags, a schema's field names, or `AgentSession(llm=openai.LLM(model="gpt-4o"))`

### Direct to MCP for facts

Factual information comes from live sources: `--help` on the installed CLI, `lk docs`, or the
[LiveKit Docs MCP server](https://docs.livekit.io/intro/mcp-server/). Skills stay conceptual and tell
agents to look up current API details instead of hardcoding them.

### Require testing

Skills that guide building an agent must send the agent on to verify its work (`debugging-livekit-agents`,
`testing-livekit-agents`). Agents shouldn't hand back untested code.

### Stay under 500 lines

Skills are loaded into agent context windows. Keep them under 500 lines so they don't crowd out the user's project context.

## File Naming Conventions

- Skill directories are gerund-form `kebab-case`: `building-livekit-agents`, `running-livekit-simulations`
- `SKILL.md` is the only uppercase filename in a skill directory
- Supporting documents go in `references/`, one level deep, with a `## Contents` list when over 100 lines

## Development Setup

Install the LiveKit CLI (`lk`) and, ideally, the Docs MCP server
(https://docs.livekit.io/intro/mcp-server/), since several skills drive them.

To check your change, run `python3 evals/validate.py`. If you touched a `description`, also run the
trigger eval in `evals/trigger/`. Both are described in [AGENTS.md](AGENTS.md#evaluating-skills).

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
