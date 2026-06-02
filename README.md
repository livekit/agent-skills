# LiveKit Agent Skills

Reusable skills for AI coding agents building with [LiveKit](https://livekit.io). These skills provide procedural knowledge that helps agents build voice AI applications more effectively.

## Available Skills

| Skill | Description |
|-------|-------------|
| **livekit-agents** | Architectural guidance for building low-latency voice AI agents with LiveKit Agents SDK. Covers workflow design, handoffs, tasks, and mandatory testing practices. |
| **livekit-simulations** | Generate targeted test scenarios for a LiveKit agent — locally, from the agent's own code plus what the user wants stress-tested — and run them as simulations. Bundles persona/goal/challenge libraries and a stdlib scenario builder. |

## Installation

```bash
npx skills add livekit/agent-skills
```

Skills activate automatically when agents detect relevant tasks (e.g., "build a voice agent", "create a LiveKit agent").

## Skill Structure

Each skill contains:
- `SKILL.md` — Agent instructions with behavioral guidance
- `references/` — Supporting documentation

## Using with MCP

These skills are designed to work alongside the [LiveKit Docs MCP server](https://docs.livekit.io/mcp). The skills provide *behavioral guidance* (how to think about building voice agents) while MCP provides *factual information* (current API signatures, configuration options).

Install the MCP server for best results. Installation instructions for all supported coding agents are available at:

**https://docs.livekit.io/intro/mcp-server/**

## Design Philosophy

These skills follow the "freeze forever" principle—they encode behavioral guidance that remains valid regardless of API changes:

- **Behavior over knowledge**: Skills teach *how to approach* problems, not API specifics
- **MCP for facts**: All factual information (API signatures, config options) comes from live documentation
- **Testing required**: Every agent implementation must include tests
- **Latency-first**: Voice AI requires different architectural thinking than text-based agents

## Contributing

Contributions welcome! When adding or modifying skills:

1. Ensure content passes the "freeze forever" test—would it still be correct if never updated?
2. Direct agents to MCP/docs for all API specifics
3. Include trigger phrases in the skill description
4. Keep skills under 500 lines for context efficiency

## License

MIT
