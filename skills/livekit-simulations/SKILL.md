---
name: livekit-simulations
description: 'Generate targeted test scenarios for a LiveKit voice or chat agent and run them as simulations — locally, from the agent''s own code plus what the user wants stress-tested. Use whenever the user wants to "test my agent", "what should I test", "create/generate simulation scenarios", "make a sim test suite", "use lk agent simulate", "stress-test the X flow", "set up scenarios for my agent", or wants to probe edge cases / refusals / regressions before shipping. Generates scenarios on the user''s machine (their code is never uploaded) and lets the user deeply steer what gets tested. Trigger even without the word "simulation" when the user clearly wants to decide what to test and verify how their agent behaves across realistic conversations. Not for building a new agent from scratch (use the livekit-agents skill), load-testing, or ordinary unit tests.'
license: MIT
metadata:
  author: livekit
  version: "0.4.0"
---

<!-- ============================================================
     BETA NOTICE — TEMPORARY. Delete this whole block (down to the
     END BETA NOTICE marker) at GA. Everything from the
     "# Generating Simulation Scenarios" heading onward is the
     permanent, production-oriented skill.
     ============================================================ -->

> **⚠️ Simulations are in private beta (not yet generally available).**
> - **No docs/MCP coverage yet.** For the `lk agent simulate` command surface,
>   use `lk agent simulate --help` and the LiveKit Cloud dashboard rather than
>   `lk docs` / MCP until simulations are documented.
> - **Recent SDK required.** Running simulations needs the 1.6 line of
>   `livekit-agents`. Confirm the installed version rather than assuming.
> - **Limited availability / auth.** Creating runs needs the project enabled for
>   simulations and a current `lk cloud auth` session. (Generating scenarios —
>   the main job of this skill — needs neither; it's fully local.)

<!-- ===================== END BETA NOTICE ====================== -->

# Generating Simulation Scenarios

The most valuable thing you can do with simulations is **generate good test scenarios for the user's agent** — grounded in the agent's actual code and in what *the user* wants stress-tested — then run them. You do this **locally**: you read the code with your normal tools (nothing is uploaded), and you (the coding agent) are the model that does the generation, so no extra API keys or services are needed.

A **scenario** = a simulated user's persona + goals (`instructions`) and the pass criteria (`agent_expectations`). A simulation plays each scenario against the agent over text and an LLM judge scores it. Your job is to produce a high-quality, diverse, *on-target* set of scenarios and write them to a YAML scenarios file the CLI can run.

## What makes this better than autopilot
A naive "just generate some tests" misses the point. Three things make this skill worth using:
1. **It reads the agent's real code** — so scenarios respect what the agent can actually do and where it blocks (especially constraints/unavailable items), instead of guessing from the name.
2. **It is steered by the user.** The user knows what they're worried about. Always capture that intent and thread it through. This is the headline — see `references/user-guidance.md`.
3. **It guarantees coverage of every risk.** Left alone, generation drifts to plausible happy-path calls and silently skips the hard cases — withholding a required field, supplying an invalid value, an empty lookup, and the guardrail/abuse surface (out-of-scope, harmful, professional-advice, sensitive-data, prompt-extraction). This skill turns the agent's constraints into an explicit **risk checklist** and requires at least one scenario per item — see `references/analyzing-the-agent.md` and `references/writing-scenarios.md`.

## The flow

1. **Describe the agent + build the risk checklist** — read its code locally and write a test-oriented description (Identity / Capabilities / **Constraints**) to `description.md`, and an explicit **risk checklist** to `risks.yaml` (one entry per must-test constraint/guardrail, each with an `id` and `category`). Follow `references/analyzing-the-agent.md`. Never upload the code.
2. **Get the user's test focus** — if they didn't say what to probe, ask. Apply it per `references/user-guidance.md` (append a `# Test Focus` to `description.md`, and bias authoring). Focus is **additive** — it deepens chosen risks but never drops the per-risk coverage floor. If they truly have no preference, generate broad and say so.
3. **Author the scenarios — at least one per risk** — write a diverse set of ~10 scenarios grounded in `description.md` and the focus, generating the persona / mood / situation variety **from your own judgment** (this version ships no attribute libraries). **Guarantee coverage**: every `risks.yaml` item gets ≥1 dedicated scenario, written with the shape that actually exercises it, and tagged with `covers: [<risk id>, …]`. Follow `references/writing-scenarios.md` (schema, the "Party A talks to the agent" rules, no prior state, no real PII, outcome-based expectations, the adversarial-shape taxonomy, the coverage check, don't write bad tests). Write them to `authored.yaml`. Add any user-pinned must-tests here too.
4. **Assemble the config (coverage-enforced)** —
   `python scripts/build_scenarios.py assemble --in authored.yaml --agent-description-file description.md --risks risks.yaml --strict --out scenarios.yaml`
   (validates the schema, **fails if any risk is uncovered**, and emits the YAML scenarios file `lk agent simulate --scenarios` loads). Fix gaps and re-run until it passes.
5. **Run it** — `lk agent simulate --scenarios scenarios.yaml` (confirm exact flags with `--help`; needs the SDK/auth noted in the beta block). Show the user the results and offer to re-roll, re-focus, or add scenarios.

Reuse saved `scenarios.yaml` files as a regression suite — re-run them after prompt/model/tool changes.

## Principles
- **Never upload the user's code.** Reading it locally is the point; it's their IP.
- **The user's intent is the differentiator** — incorporate it every time; don't silently autopilot.
- **Ground every scenario in the description**, especially Constraints — a scenario the agent can't possibly satisfy (or a guardrail it *should* refuse) must have expectations that reflect that.
- **The script is deterministic glue; you are the generator.** Let `build_scenarios.py` handle assembly + the coverage check; you do the reading, the judgement, the diversity, and the authoring.

## Verify, don't invent (freeze-forever)
This skill is the method (no bundled libraries — you supply diversity yourself). The exact `lk agent simulate` flags, the CI wait/fail flag, the minimum SDK version, and the dashboard come from live sources because they change — use `lk agent simulate --help` and (post-beta) `lk docs` / the LiveKit MCP server. A wrong flag wastes a run; look it up rather than guessing.

## After running: acting on results (secondary)
Once a run completes, read the per-scenario pass/fail, the run summary, and the transcripts of failures. Fix the agent where a failure is real (and re-run); recognize when a failure is actually a bad scenario and fix the scenario instead. Keep this lightweight — modern models are already good at the fix step; the durable value of this skill is the scenarios you generate and keep.
