---
name: livekit-agents-production
description: 'Extend, debug, and operate existing LiveKit agent codebases in production. Use when contributing to an established voice agent project, debugging call issues, optimizing latency, adding providers or modules, handling async patterns in worker processes, or operating LiveKit agents at scale. Complements the livekit-agents skill which covers building from scratch.'
license: MIT
metadata:
  author: livekit
  version: "0.1.0"
---

# LiveKit Agents: Extending and Operating Existing Codebases

This skill provides guidance for developers working within an established LiveKit agent codebase — adding features, debugging production issues, optimizing performance, and operating agents at scale. It complements the `livekit-agents` skill, which covers building agents from scratch.

The principles here are drawn from production experience and encode *how to work effectively* within an existing agent architecture. All factual information about APIs, methods, and configurations must come from live documentation.

## MANDATORY: Before Writing Any Code

1. **Read this entire skill document** — do not skip sections even if MCP is available
2. **Read the project's own documentation first** — existing codebases have conventions, architectural decisions, and constraints that override general guidance. Look for README files, architecture docs, and inline documentation before making changes
3. **Read 2-3 similar modules** before writing a new one — understand the patterns already established in the codebase
4. **Verify all LiveKit APIs against live docs** — never rely on model memory. Use the LiveKit MCP server if available, otherwise use web search against docs.livekit.io. See the `livekit-agents` skill and `references/freshness-rules.md` for detailed verification guidance
5. **Plan to write tests** — every change must include tests that work within the project's existing test infrastructure

## Part 1: Voice Agent Design Principles

These principles apply to every change you make, whether adding a feature, fixing a bug, or refactoring. They are the lens through which all decisions should be evaluated.

### Latency Is the Primary Constraint

Voice conversations are real-time. Users expect responses within hundreds of milliseconds. Every change you make should be evaluated for latency impact:

- Will this add round-trip time to the audio pipeline?
- Does this block the event loop during active conversation?
- Could this cause an audible pause for the user?

Latency issues compound. A change that adds "just 200ms" in development may combine with network conditions, provider variability, and other overhead to create a noticeably degraded experience in production. Measure latency impact before and after your changes.

### Context Bloat Kills Performance

Large system prompts and extensive tool lists directly increase LLM inference time. When modifying prompts, tools, or agent instructions:

- Adding a tool has a cost — each tool in the context increases latency for every LLM call, not just the calls that use that tool
- Growing the system prompt affects every turn of conversation, not just the first
- For long-running conversations, unbounded context growth means progressively slower responses as the call continues

Design changes with minimal viable context. If you are adding a capability, consider whether it should be scoped to a specific conversation phase rather than available globally.

### Users Don't Read, They Listen

Voice interface constraints differ fundamentally from text. When modifying agent responses or behavior:

- Long responses frustrate users — keep outputs concise
- Users cannot scroll back — ensure clarity on first delivery
- Interruptions are normal — design for graceful handling
- Silence feels broken — if processing takes time, acknowledge it

---

## Part 2: The Worker Process Model

Understanding the worker process model is essential for writing correct agent code. Misunderstanding it is the single most common source of production bugs.

### Parent-Child Process Architecture

LiveKit agent workers typically follow a parent-child model. The parent process starts, initializes shared resources, and spawns child processes (or contexts) for individual call sessions. This architecture has critical implications:

**Shared state inheritance.** Resources initialized in the parent are available to all children. This is the foundation of prewarming — load heavy resources once so every session inherits them without re-initialization. However, all shared resources must be read-only or concurrency-safe. Mutating shared state from child processes leads to unpredictable behavior.

**Async context inheritance.** The parent process typically has an active event loop managed by the framework. Child processes inherit references to the parent's async primitives (events, locks, futures, tasks). Creating a new event loop in a child process while inherited primitives still reference the parent's loop causes conflicts that are difficult to diagnose.

### Safe Async Patterns

The interaction between worker processes and async execution is where most production bugs originate. The rules are:

**Never create a new async runtime inside a worker's child process.** The framework manages the event loop. If you need to perform async work during initialization, use the framework's existing async context — either through lazy loading (fetch on first access in an already-async method) or through a two-phase init pattern (constructor sets up state, a separate async method performs initialization and is awaited by the caller).

**Never block on async calls from synchronous constructors.** Module constructors in agent code run within the worker's process. Blocking on an async call from a synchronous context (to force-wait for a result) risks deadlocking the event loop or creating a conflicting secondary loop.

**Recognize the symptoms.** When you see errors about events bound to different loops, loops already running, tasks destroyed while pending, or loops that cannot be reused — the root cause is almost always an async context conflict in the worker process model. Trace back to where a new async runtime or blocking call was introduced.

### Prewarming Strategy

Prewarming is the practice of loading expensive resources in the parent process before child sessions are created. This trades parent memory for child startup speed.

**What to prewarm:** Models that take significant time to load (VAD, turn detection), clients that establish persistent connections, and static assets that every session will need.

**What not to prewarm:** Resources that are session-specific, resources that hold mutable state, and resources whose memory cost outweighs the startup time savings. Every byte loaded in the parent is reflected in every child's memory footprint, even if the actual physical memory is shared through copy-on-write.

**Validate prewarm effectiveness.** After prewarming a resource, verify that child processes actually use the prewarmed instance rather than creating a new one. A common mistake is prewarming a resource but then having the child's initialization code ignore it and load a fresh instance anyway.

---

## Part 3: Provider Architecture

Voice agents depend on multiple external providers (STT, TTS, LLM, VAD). Managing their lifecycle affects both startup latency and runtime reliability.

### Provider Initialization

Provider clients that establish network connections or load model weights add latency on first use. When adding or modifying provider integrations:

- Determine whether the provider can be prewarmed or whether lazy initialization with connection pooling is more appropriate
- Measure the cold-start cost — the time between requesting the first operation and receiving the first result
- Consider the memory trade-off — prewarming reduces latency but increases the baseline memory footprint of every worker process

### Provider Failure Handling

Providers will fail in production — API rate limits, network timeouts, model overload, service outages. When working with provider integrations:

- Configure appropriate timeouts — a provider call that hangs indefinitely is worse than one that fails fast
- Design for graceful degradation rather than hard failure — the user should hear a meaningful response, not silence
- Distinguish between transient failures (worth retrying) and persistent failures (require escalation or fallback)
- Log provider response times — latency degradation is often the first sign of an impending outage

### Adding a New Provider

When adding a new provider to an existing codebase:

1. Check whether the SDK already has a plugin for the provider — consult the documentation
2. Study how existing providers are integrated in the codebase — follow the same patterns for initialization, configuration, and error handling
3. Ensure the new provider's configuration flows through the same config pipeline as existing providers
4. Test with realistic latency conditions, not just happy-path responses

---

## Part 4: Testing Within an Existing Codebase

Every change must include tests. But in an existing codebase, the challenge is not "how to set up testing" — it is "how to write tests that fit the established infrastructure."

### Use What Exists

Before writing any test, examine the project's existing test setup:

- **Test directory structure** — understand where unit tests, integration tests, and functional tests live
- **Fixture infrastructure** — most mature agent codebases have factories or fixtures for creating mock SDK objects. Use them rather than creating parallel infrastructure
- **Mock patterns** — understand how the project mocks external services (gateways, APIs, providers) and follow the same approach

Creating a second way to do something that already exists introduces maintenance burden and confuses future contributors.

### Mock at Boundaries, Execute Real Code

Tests should exercise actual module logic. Mock external dependencies at the boundary — the gateway call, the provider API, the database query — not the code under test. If you find yourself mocking internal methods of the module you are testing, the test is not verifying real behavior.

### Understand SDK Test Primitives

The LiveKit SDK provides different context objects for different purposes — job-level contexts, run-level contexts, and session objects are distinct types with different interfaces and lifecycles. Using the wrong mock type produces tests that pass but do not reflect real behavior. Consult the SDK documentation for current testing utilities, and study how the existing codebase mocks these objects.

### Async Testing

All agent code is async. Tests must handle async execution properly:

- Use async-compatible test frameworks and runners
- Use async-compatible mock objects for any method that returns a coroutine — a standard synchronous mock will not behave correctly when awaited
- Ensure test teardown properly cleans up async resources to prevent warnings about pending tasks

---

## Part 5: Performance and Optimization

### Measure Before Optimizing

When investigating or improving agent performance, always measure before changing:

- **Time-to-first-audio** — the interval from when the user finishes speaking to when they hear the agent begin responding. This is the metric users feel most directly
- **Initialization latency** — break startup into phases (connection, provider init, first dialogue) to identify which phase dominates
- **Tool execution time** — slow tool calls create audible pauses. Identify which tools block the conversation pipeline
- **Context size over time** — monitor how the conversation context grows during long calls. Unbounded growth means progressively increasing latency

### Common Performance Anti-Patterns

When reviewing or modifying agent code, watch for:

- **Synchronous I/O in async context** — a synchronous HTTP call or file read blocks the entire event loop, freezing audio processing for all concurrent operations in that process
- **On-demand loading during calls** — loading a model or establishing a connection during an active call adds latency the user directly experiences. Move these to prewarm or session setup
- **Unbounded context accumulation** — full conversation history without summarization means every LLM call gets slower as the conversation progresses
- **Global tool registration** — registering all available tools regardless of conversation phase increases inference time for every LLM call

### Endpointing and Turn Detection

Endpointing (detecting when a user has finished speaking) and turn detection are critical tuning parameters that directly affect perceived agent quality:

- **Too aggressive** — the agent interrupts users mid-sentence or mid-thought, creating frustration
- **Too conservative** — long pauses after the user stops speaking, making the agent feel slow and unresponsive

These parameters are highly use-case dependent. A customer support agent handling complex queries needs more conservative endpointing (users pause to think), while a quick-answer assistant benefits from aggressive detection. When modifying these parameters, test with realistic conversation patterns that match your use case, not just scripted inputs.

---

## Part 6: Production Operations

### Debugging Common Failures

**Async and event loop errors** — the most common class. Errors about events bound to different loops, loops already running, or destroyed tasks almost always trace back to creating new async runtimes in worker child processes or blocking on async calls from synchronous code. See Part 2 for the underlying cause.

**Provider timeouts and degradation** — check provider-specific response times and error codes. Distinguish between transient failures (single request timeout) and systemic degradation (increasing latency trend). Log provider response times to detect degradation before it becomes a full outage.

**Silent tool failures** — tools that throw exceptions during a call may be caught by the framework without surfacing clearly to the user. Ensure tools have explicit error handling and return meaningful feedback rather than failing silently.

**Connection instability** — WebSocket disconnects, room reconnection failures, and participant state inconsistencies. Log connection state changes and understand the SDK's built-in reconnection behavior before adding custom retry logic.

### Graceful Shutdown

In production, worker processes receive termination signals during deployments, scaling events, and restarts. Without proper shutdown handling, active calls are dropped:

- Allow in-progress call sessions to complete rather than terminating immediately
- Ensure post-call cleanup (state updates, event publishing, recording finalization) completes even during shutdown
- Coordinate shutdown grace periods with your deployment orchestrator — an agent that needs 30 seconds to drain must have a termination grace period of at least 30 seconds

### SDK Upgrade Strategy

The LiveKit Agents SDK evolves rapidly and makes breaking changes across versions. Approach upgrades methodically:

- **Pin SDK versions** in your dependency file — never use unpinned or wildcard versions in production
- **Read changelogs before upgrading** — look for breaking changes, deprecated APIs, and migration guides
- **Upgrade in isolation** — update the SDK in a branch, run your full test suite, and verify behavior before merging
- **Test with real conversations** after upgrading — some regressions only surface during actual voice interaction, not in unit tests
- **Monitor after deployment** — watch latency metrics, error rates, and provider behavior for the first hours after an SDK upgrade

### Observability

Production agents need structured observability:

- **Correlate logs by session** — every log entry during a call should include the session or call identifier so that a single call's lifecycle can be traced end-to-end
- **Instrument phase boundaries** — log timing at key lifecycle moments (connection established, first user speech detected, first agent response sent) to identify where latency is introduced
- **Track provider metrics separately** — provider latency, error rates, and throughput should be visible independently so that a degrading provider can be identified without digging through application logs

---

## When to Consult Documentation vs. This Skill

**Always consult live documentation for:**
- API method signatures and parameters
- Configuration options and their valid values
- SDK version-specific features or changes
- Provider integration details and plugin availability
- CLI commands and flags

**This skill provides guidance on:**
- Working effectively within an existing agent architecture
- The worker process model and its async implications
- Provider lifecycle management
- Performance optimization methodology
- Testing within established infrastructure
- Production operational patterns

The distinction matters: this skill tells you *how to work within* a LiveKit agent codebase. The documentation tells you *what the SDK APIs do*. The `livekit-agents` skill tells you *how to build from scratch*.

## Summary

Contributing effectively to an existing LiveKit agent codebase requires:

1. **Understand before changing** — read existing patterns, conventions, and documentation before writing new code
2. **Respect the process model** — understand parent-child worker architecture and async context inheritance to avoid the most common production bugs
3. **Evaluate every change for latency impact** — voice is real-time and users feel every added millisecond
4. **Manage provider lifecycles deliberately** — prewarm what you can, handle failures gracefully, measure cold-start costs
5. **Test within the existing infrastructure** — use established fixtures and patterns, mock at boundaries, handle async correctly
6. **Measure before optimizing** — profile initialization phases, tool execution, and context growth before making performance changes
7. **Operate defensively** — graceful shutdown, SDK version pinning, structured observability, and proactive debugging patterns
8. **Verify everything** against live documentation — never trust model memory for LiveKit APIs
