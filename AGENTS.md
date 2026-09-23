# AGENTS.md

This repository publishes [Agent Skills](https://agentskills.io) that teach coding agents to build,
test, and ship voice agents with LiveKit. If you are an agent working *in this repo*, your job is
to write and evaluate skills, not to build a LiveKit agent — this file is for you.
[README.md](README.md) is for the people who install the skills.

## Repository map

```
agent-skills/
├── README.md                       # for users: what the skills do, how to install
├── AGENTS.md                       # for agents maintaining the repo (this file)
├── CONTRIBUTING.md                 # for human contributors: process
├── skills/                         # the published skills — pushes here sync downstream
│   ├── reading-livekit-docs/
│   ├── building-livekit-agents/
│   ├── debugging-livekit-agents/
│   ├── testing-livekit-agents/
│   ├── writing-livekit-scenarios/
│   │   └── references/             # scenario craft, risk coverage, connecting the agent
│   ├── running-livekit-simulations/
│   ├── livekit-agents/             # DEPRECATED stub (see "Deprecating a skill")
│   └── livekit-simulations/        # DEPRECATED stub
└── evals/                          # tooling for checking the skills — never under skills/
    ├── validate.py                 # structural checks on every SKILL.md
    ├── trigger/                    # does the right skill fire for a request?
    └── output/                     # does following a skill produce better work?
```

## How the skill set is meant to work

Each skill owns one job and names its siblings for adjacent jobs. Routing happens in the
`description` fields, which are the only part of a skill loaded before it fires — so a request
should land on exactly one skill, and that skill's body should be everything needed for its job.

| Skill | Owns | Hands off to |
|---|---|---|
| reading-livekit-docs | Looking up any LiveKit fact | — (every other skill loads it first) |
| building-livekit-agents | Architecture and voice-specific design | debugging, testing |
| debugging-livekit-agents | Live-testing during development (`lk agent debugger`) | testing (to pin a bug), running (for speech issues) |
| testing-livekit-agents | Turn-level tests in pytest/Vitest | debugging (to find the bug), running (whole conversations) |
| writing-livekit-scenarios | Authoring scenarios, and the agent-side code that consumes them | running |
| running-livekit-simulations | Running simulations, CI, triage | writing (bad scenario), testing (repeat failure) |

A bare "test my agent" goes to **debugging** by design — it's the cheap, local path; running
simulations spends cloud resources.

## Authoring rules

These exist because the skills must stay correct without maintenance. Every rule below has been
violated in this repo once already; that's how it got written down.

**Encode behavior, not knowledge.** A skill teaches how to approach a job — what to check, what
goes wrong, which tool fits — never the API surface. Allowed: one simple example command with a
`# see --help` comment. Not allowed: a flag roster, a schema field list, a list of built-in helpers,
a JSON output shape, version numbers, minimum versions, or "as of writing". Those go stale within
months; the skill should say it *deliberately doesn't restate them* and point at `--help` and
`reading-livekit-docs`. When you catch yourself typing a backticked identifier, ask whether the
sentence still works as a concept.

**No time-relative phrasing.** "Newer CLIs", "is landing", "still moving", "recently" all become
false. Write capability checks instead: "where the CLI supports X, …", "if the command offers to Y,
accept."

**Stay atomic.** One job per skill. Cross-link by name instead of restating; two skills that both
explain simulations compete for the same triggers and dilute both.

**Descriptions are written as a set.** The description is the whole trigger mechanism. For each one:
third person ("Runs simulations…", never "Run simulations…" or "I can run…" — the platform docs
warn this breaks discovery); the phrases a user actually types for *that* job; the sibling to use
for adjacent jobs; a negative clause where two skills genuinely border ("Not the default for a bare
'test my agent' — that is debugging-livekit-agents"); at most 1,024 characters. Be a little pushy —
models under-trigger skills. When you change one description, re-read the others; then run the
trigger eval.

**Names are gerunds** — `building-livekit-agents`, `running-livekit-simulations` — lowercase,
hyphens, under 64 characters, no "claude" or "anthropic". The platform docs recommend this form;
what matters more is that the set is consistent.

**Bodies stay under 500 lines; references are one level deep.** Anything long or conditional goes
in `references/`, linked directly from SKILL.md with a sentence saying when to read it. A reference
over 100 lines starts with a `## Contents` list so a partial read still shows its scope.

**Frontmatter:**

```yaml
---
name: running-livekit-simulations
description: 'Runs LiveKit agent simulations and acts on the results. Use when the user says "run my simulations", … For authoring the scenarios use writing-livekit-scenarios.'
license: MIT
metadata:
  author: livekit
  version: "1.0.0"
---
```

**Explain why, not just what.** The skills are read by capable models. "Restart after every edit —
a running session holds the old code" lands; "ALWAYS restart" doesn't. If you're writing a
capitalized MUST, reframe it as the reason.

## Verifying facts while you write

Even a conceptual skill rests on facts: that a subcommand exists, that a callback can only fail a
run, that generation uploads source. Verify each one in the session, in this order:

1. **`--help` on the installed CLI.** Outranks every document.
2. **`lk docs` or the Docs MCP server** for the published behavior.
3. **The public repos for what's in flight** — [livekit/livekit-cli](https://github.com/livekit/livekit-cli)
   and [livekit/agents](https://github.com/livekit/agents), including open PRs. The surface
   regularly ships ahead of the docs and behind the source; a skill written from live docs alone
   has been wrong on arrival here before.
4. **The examples in livekit/agents** for how things are actually used (the front-desk and hotel
   receptionist examples are the canonical scenario files).

Then write the *shape* you verified, not the surface. If a fact only holds for one version, it
doesn't belong in a skill.

## Evaluating skills

Run these before opening a PR. The first is mandatory; the second is mandatory when any
`description` changed; the third is for new or substantially rewritten skills.

### 1. Structure — `python3 evals/validate.py`

Checks every `skills/*/SKILL.md`: frontmatter fields, name matches directory, description length
and third person, body length, references exist and have a TOC when long, no dangling
cross-references to skills that don't exist, no time-relative phrasing. Exit code is non-zero on
any failure. Cheap; run it constantly.

### 2. Triggering — `evals/trigger/`

The question atomic skills most often get wrong: *does the right one fire?* The harness installs
the whole set into a scratch copy of a testbed project, runs each query in `queries.json` through
`claude -p`, and records which skill was invoked first. Queries are labeled with the acceptable
skill(s), or none for near-misses that must not trigger anything. Output is a per-group confusion
table and a list of misses.

```bash
python3 evals/trigger/run.py                    # fixture: agent-starter-python, cloned fresh
python3 evals/trigger/run.py --template node    # the skills serve both languages; run both
```

Read `evals/trigger/README.md` for options (subset by index, runs per query, model). Add a query
whenever you find a request that routed wrong; the near-miss cases are the valuable ones.

**Fixtures and the user's LiveKit project.** Evals build their fixture by shallow-cloning a public
`livekit-examples` starter — not with `lk agent init` or `lk app create`, which resolve a LiveKit
Cloud project first and write its credentials into the directory. The harness strips `.env*` files
and injects dummy `LIVEKIT_*` variables into every subprocess, which `lk` and the SDKs honour over
the user's configured default project, so an eval can't spend inference or upload source against
whichever project the user last selected. The model doing the deciding in every eval is the user's
Claude; LiveKit Inference is never involved unless an agent executes the agent under test, which the
guards prevent.

Only the repo's skills are visible to trigger runs, which is what you want for measuring collisions
within the set — but your users will have other skills installed, so a real-setup run is worth doing
occasionally.

### 3. Output — `evals/output/`

Does following the skill produce better work than not following it? Run the same realistic prompt
twice — once with the skill path given to a fresh agent, once without — against a fixture built the
same way the trigger harness builds one (a credential-stripped clone of a starter template), and
grade the outputs.

`evals/output/grade_scenarios.py <outputs> --agent <src/agent.py|src/agent.ts>` grades scenario
files in two layers. **Structural** checks are exact — YAML parses, keys match the CLI's scenario
struct, required fields, group names, quick/full split. **Judged** checks are one `claude -p` call
with no tools that reads the agent's source and the scenarios and returns per-assertion verdicts
with quoted evidence: every constraint in the agent's instructions is exercised, refusals are the
pass, no invented capabilities, no rotting dates, expectations are decidable, the simulated user
never plays the agent. Judgment questions get a judge; an earlier regex version false-negatived on
good work and was replaced. Verdicts vary a little — use `--judge-runs 2` or `3` and read the
evidence rather than counting passes. `evals/output/README.md` has the details and the safety rules
for output-eval agents, which need write tools.

Two things learned the hard way:

- **Testbeds confound.** Both starter templates ship a `scenarios.yaml` that already uses the
  instructions template the skill teaches. A baseline run copies it and looks nearly as good as the
  skill run. Check what the fixture already contains before reading a null result as "the skill adds
  nothing."
- **Never let an eval agent run `lk agent simulate`** without a scenario file. It uploads the
  fixture's source to LiveKit Cloud and spends real inference. Eval prompts must say so, and the
  dummy `LIVEKIT_*` environment must be set for any agent with shell access.

### Definition of done for a skill change

- `validate.py` passes.
- Descriptions changed → trigger eval run, no new misses, and the run's summary pasted in the PR.
- New or rewritten skill → an output eval with at least three prompts, results summarized in the PR.
- Nothing in the body would be wrong if the CLI added a flag or renamed a helper tomorrow.

## Deprecating a skill

Don't delete a skill directory. Replace its `SKILL.md` with a stub whose description begins
`DEPRECATED — do not use.` and names the replacements, with a table in the body mapping old jobs to
new skills. Remove its `references/` and `scripts/` — stale supporting files are actively harmful.
Two reasons for the stub: agents that installed the old name still resolve it, and pushes to
`skills/**` dispatch a downstream sync (`.github/workflows/trigger-skill-sync.yml`) whose handling
of a removed directory isn't guaranteed.

Rename by the same route: new directory, old one becomes a stub.

## Things not to do here

- Don't put evals, tooling, or scratch files under `skills/`. Everything there is published and
  synced.
- Don't add a skill because a topic exists. Add one because agents demonstrably do that job badly
  without it, and you can say what the skill changes.
- Don't tune a description to one failing query. Ask what class of request it represents.

## Links

- [Agent Skills format](https://agentskills.io) · [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [LiveKit docs](https://docs.livekit.io) · [Docs MCP server](https://docs.livekit.io/intro/mcp-server/)
- [livekit/agents](https://github.com/livekit/agents) · [livekit/livekit-cli](https://github.com/livekit/livekit-cli)
