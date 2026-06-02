# Analyzing the agent → a test-oriented description

Before generating scenarios you need a tight, behavioral description of the agent under test. You produce it by **reading the agent's code locally** with your normal file tools — the code never leaves the machine and nothing is uploaded. (This replaces the old cloud "code analysis" service.)

The description has exactly one purpose: **helping scenario generation produce realistic test cases.** A simulated user never reads docs — they arrive with a need and interact. So the description must make clear what needs are serviceable, what flows they must go through, and where they will hit walls.

## Output: three sections, Constraints-first

Write the description as markdown with these sections. **Prioritize Constraints — a missed constraint produces invalid scenarios.** Keep it concise and dense.

```
# Identity
Name and role of the agent. What is the service? What does someone interacting with it experience?

# Capabilities
What the user can request and have done:
- Types of requests (inquiries, bookings, payments, modifications, ...)
- Domain structure the user must know (how products/services are organized, what categories exist)
- Key information the agent collects or provides

# Constraints
Where requests get blocked, denied, or require more than expected. Be specific:
- Mandatory preconditions (what must happen before X)
- Multi-step flows that cannot be skipped
- Services this agent explicitly cannot provide
- Unavailable items/plans/features — enumerate EACH by name ("X is currently unavailable").
  A general rule ("unavailable items won't be offered") is not enough. Unavailable items must
  NOT appear under Capabilities — filter so only currently-active items are listed there.
- Hard limits (caps, time windows, eligibility rules)
```

## How to read the code (scope rule — apply before reading anything else)

1. **Read the entrypoint first.** Identify which agent class is passed to `session.start()` — that is the deployed agent.
2. **In scope:** that agent plus anything reachable from it during a live session — agents returned by function tools (an `update_agent` transition), agents passed to `session.update_agent()`, and `AgentTask`s awaited inside tools/lifecycle hooks.
3. **Out of scope:** other agent classes, imported-but-unused modules, example files, anything in the same directory not reachable from `session.start()`. Exclude it entirely, no matter how relevant it looks.
4. Read the deployed agent's instructions string and its helper/implementation files — helpers often encode hard constraints (availability, required inputs, caps) the prompt doesn't state. Test files are secondary confirmation only.
5. **Capture implicit capabilities too** — a capability stated only in the instructions string (answering questions about a menu, policy, hours) is real even with no dedicated tool.

## Write from the user's perspective — and leave out the internals

Describe what the user can ask and what the agent does for them. **Do NOT include:**
- Internal identifiers, parameter names, or data structures (say "users can remove items from their order," not "requires an order item ID").
- References to code files, modules, backends, or implementation choices (which DB/calendar is used).
- Observations about code structure, dead code, or what's present-but-inactive — only state what IS and ISN'T available to users.
- How errors are handled internally.
- Capabilities inferred from the agent's name or industry convention — only what the code actually implements.

When the agent always prompts for a detail but the user may decline it, describe that detail as **optional** (from the user's perspective they aren't required to choose it).

**No function tools at all?** Some agents are instruction-only (no `@function_tool`). When that's the case, state it explicitly under Constraints — e.g. "no backend or account lookup; cannot retrieve, confirm, or act on any stored data." Scenarios must respect that such an agent can only converse and guide, never look something up or perform a backend action.

## Verify before you finish
- Multi-tier orders/services: captured every mandatory component and its exact constraints (required items, size limits)?
- Unavailable items: listed by name under Constraints? (Don't claim the agent suggests alternatives unless the code implements that.)
- Required explicit inputs (variants, sizes): stated under Constraints?

Save the finished description to a file (e.g. `description.md`) — scenario generation and `assemble` both consume it.
