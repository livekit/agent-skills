# AGENTS.md

This repository publishes [Agent Skills](https://agentskills.io) that teach coding agents to build,
test, and ship voice agents with LiveKit. This file is for agents working *in this repo*, where the
job is writing and evaluating skills rather than building a LiveKit agent.
[README.md](README.md) is for the people who install the skills.

## Repository map

```
agent-skills/
├── README.md                       # for users: what the skills do, how to install
├── AGENTS.md                       # for agents maintaining the repo (this file)
├── CONTRIBUTING.md                 # for human contributors: process
├── skills/                         # the published skills; this layout is the install contract
│   ├── reading-livekit-docs/
│   ├── building-livekit-agents/
│   ├── debugging-livekit-agents/
│   ├── testing-livekit-agents/
│   ├── writing-livekit-scenarios/
│   │   └── references/             # scenario craft, risk coverage, connecting the agent
│   └── running-livekit-simulations/
└── evals/                          # tooling for checking the skills — never under skills/
    ├── validate.py                 # structural checks on every SKILL.md
    ├── trigger/                    # does the right skill fire for a request?
    └── output/                     # does following a skill produce better work?
```

## How the skill set is meant to work

Each skill owns one job and names its siblings for adjacent jobs. Routing happens in the
`description` fields, which are the only part of a skill loaded before it fires. A request should
land on exactly one skill, and that skill's body should cover everything needed for its job.

| Skill | Owns | Hands off to |
|---|---|---|
| reading-livekit-docs | Looking up any LiveKit fact | — (every other skill loads it first) |
| building-livekit-agents | Architecture and voice-specific design | debugging, testing |
| debugging-livekit-agents | Live-testing during development (`lk agent debugger`) | testing (to pin a bug), running (for speech issues) |
| testing-livekit-agents | Turn-level tests in pytest/Vitest | debugging (to find the bug), running (whole conversations) |
| writing-livekit-scenarios | Authoring scenarios, and the agent-side code that consumes them | running |
| running-livekit-simulations | Running simulations, CI, triage | writing (bad scenario), testing (repeat failure) |

A bare "test my agent" goes to **debugging**. That's the cheap, local path; running simulations
spends cloud resources.

## Authoring rules

The skills need to stay correct without maintenance, and each rule below exists because this repo
broke it at least once.

**Encode behavior, not knowledge.** A skill teaches how to approach a job (what to check, what goes
wrong, which tool fits), not the API surface. You can include one simple example command with a
`# see --help` comment. Don't include a flag roster, a schema field list, a list of built-in
helpers, a JSON output shape, version numbers, minimum versions, or "as of writing". Those go stale
within months. Instead, the skill should say it doesn't restate them and point at `--help` and
`reading-livekit-docs`. When you're about to type a backticked identifier, check whether the
sentence would still work as a concept.

**No time-relative phrasing.** Phrases like "newer CLIs", "is landing", "still moving", and
"recently" stop being true. Write capability checks instead: "where the CLI supports X, …", "if the
command offers to Y, accept."

**Stay atomic.** One job per skill. Cross-link by name instead of restating. Two skills that both
explain simulations compete for the same triggers, and both get weaker.

**Descriptions are written as a set.** The description is the entire trigger mechanism. Each one
needs:

- third person ("Runs simulations…", never "Run simulations…" or "I can run…"; the platform docs
  warn that other forms break discovery)
- the phrases a user types for *that* job
- the sibling to use for adjacent jobs
- a negative clause where two skills border each other ("Not the default for a bare 'test my
  agent', which goes to debugging-livekit-agents")
- at most 1,024 characters

Lean toward pushy, since models tend to under-trigger skills. When you change one description,
re-read the others, then run the trigger eval.

**Names are gerunds**: `building-livekit-agents`, `running-livekit-simulations`. Lowercase, hyphens,
under 64 characters, no "claude" or "anthropic". The platform docs recommend this form, but
consistency across the set matters more.

**Bodies stay under 500 lines; references are one level deep.** Put anything long or conditional in
`references/`, linked directly from SKILL.md with a sentence saying when to read it. A reference
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

**Say "self-hosted" only about the agent.** A self-hosted agent runs on the user's own servers
instead of LiveKit Cloud's agent hosting, and it can still use LiveKit Cloud features such as
LiveKit Inference. When the user runs the LiveKit server themselves, call it LiveKit OSS, as
opposed to LiveKit Cloud. Using "self-hosted" for both leads agents to wrongly rule out Cloud
features for anyone who hosts their own agent.

**Explain why.** Capable models read these skills, and they respond better to a reason than to a
bare command. "Restart after every edit — a running session holds the old code" works better than
"ALWAYS restart". If you find yourself writing a capitalized MUST, replace it with the reason.

## Verifying facts while you write

Even a conceptual skill depends on facts: that a subcommand exists, that a callback can only fail a
run, that generation uploads source. Verify each one during the session, in this order:

1. **`--help` on the installed CLI.** This outranks every document.
2. **`lk docs` or the Docs MCP server** for the published behavior.
3. **The public repos for unreleased work**: [livekit/livekit-cli](https://github.com/livekit/livekit-cli)
   and [livekit/agents](https://github.com/livekit/agents), including open PRs. The CLI and SDK
   often ship ahead of the docs and behind the source. Skills written from the live docs alone have
   been wrong on arrival here before.
4. **The examples in livekit/agents** for how things are used in practice (the front-desk and hotel
   receptionist examples are the canonical scenario files).

Then write down the *shape* of what you verified, not the specific surface. If a fact only holds
for one version, it doesn't belong in a skill.

## Evaluating skills

Run these before opening a PR. The first is always required. The second is required when any
`description` changed. The third is for new or substantially rewritten skills.

### 1. Structure — `python3 evals/validate.py`

Checks every `skills/*/SKILL.md` for: frontmatter fields, name matching the directory, description
length and third person, body length, references that exist and have a TOC when long, no dangling
cross-references to skills that don't exist, and no time-relative phrasing. Exits non-zero on any
failure. It's cheap, so run it often.

### 2. Triggering — `evals/trigger/`

This checks whether the right skill fires, which is what atomic skills most often get wrong. The
harness installs the whole set into a scratch copy of a testbed project, runs each query in
`queries.json` through `claude -p`, and records which skill was invoked first. Each query is
labeled with the acceptable skill(s), or with none for near-misses that shouldn't trigger anything.
Output is a per-group confusion table and a list of misses.

```bash
python3 evals/trigger/run.py                    # fixture: agent-starter-python, cloned fresh
python3 evals/trigger/run.py --template node    # the skills serve both languages; run both
```

See `evals/trigger/README.md` for options (subset by index, runs per query, model). When you find a
request that routed wrong, add it as a query. Near-miss cases are the most valuable ones.

**Fixtures and the user's LiveKit project.** Evals build their fixture by shallow-cloning a public
`livekit-examples` starter. They don't use `lk agent init` or `lk app create`, because those resolve
a LiveKit Cloud project first and write its credentials into the directory. The harness strips
`.env*` files and injects dummy `LIVEKIT_*` variables into every subprocess. `lk` and the SDKs
honour those over the user's configured default project, so an eval can't spend inference or upload
source against whichever project the user last selected. The model making the decisions in every
eval is the user's Claude. LiveKit Inference is only involved if an agent executes the agent under
test, and the guards prevent that.

Trigger runs only see the repo's skills. That's what you want for measuring collisions within the
set, but users will have other skills installed, so it's worth occasionally doing a run with a
normal setup.

### 3. Output — `evals/output/`

This checks whether following the skill produces better work than not following it. Run the same
realistic prompt twice, once with the skill path given to a fresh agent and once without, against a
fixture built the same way as the trigger harness's (a credential-stripped clone of a starter
template). Then grade the outputs.

`evals/output/grade_scenarios.py <outputs> --agent <src/agent.py|src/agent.ts>` grades scenario
files in two layers.

- **Structural** checks are exact: YAML parses, keys match the CLI's scenario struct, required
  fields, group names, quick/full split.
- **Judged** checks are one `claude -p` call with no tools. It reads the agent's source and the
  scenarios and returns per-assertion verdicts with quoted evidence. The assertions: every
  constraint in the agent's instructions is exercised, refusals count as the pass, no invented
  capabilities, no dates that will go stale, expectations are decidable, and the simulated user
  never plays the agent.

These questions need judgment, so they get a judge. An earlier regex version gave false negatives
on good work and was replaced. Verdicts vary a little between runs, so use `--judge-runs 2` or `3`
and read the evidence instead of counting passes. `evals/output/README.md` has the details and the
safety rules for output-eval agents, which need write tools.

Two lessons from past runs:

- **Testbeds confound.** Both starter templates ship a `scenarios.yaml` that already uses the
  instructions template the skill teaches. A baseline run copies it and looks nearly as good as the
  skill run. Check what the fixture already contains before concluding the skill adds nothing.
- **Never let an eval agent run `lk agent simulate`** without a scenario file. It uploads the
  fixture's source to LiveKit Cloud and spends inference. Eval prompts must say so, and the dummy
  `LIVEKIT_*` environment must be set for any agent with shell access.

### Definition of done for a skill change

- `validate.py` passes.
- Descriptions changed → trigger eval run, no new misses, and the run's summary pasted in the PR.
- New or rewritten skill → an output eval with at least three prompts, results summarized in the PR.
- Nothing in the body would be wrong if the CLI added a flag or renamed a helper tomorrow.

## Removing or renaming a skill

Delete the directory. To rename, create the new directory and delete the old one. Don't leave a
stub behind: a stub's description is loaded into every user's context on every request, forever,
to say "don't use me" — the opposite of what the set is trying to do for context.

Skills are installed from this repository — `npx skills add livekit/agent-skills` today, and the
LiveKit CLI. Installers take `skills/<name>/SKILL.md` plus that skill's `references/`, so keep that
layout stable: a renamed directory is a removed skill and a new one, and nothing here can reach a
user's existing local copy. The README tells users of a removed skill to reinstall.

## Things not to do here

- Don't put evals, tooling, or scratch files under `skills/`. Everything there is published; installers take the whole directory.
- Don't add a skill because a topic exists. Add one when agents do that job badly without it
  and you can say what the skill changes.
- Don't tune a description to fix one failing query. Figure out what class of request it represents.

## Links

- [Agent Skills format](https://agentskills.io) · [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [LiveKit docs](https://docs.livekit.io) · [Docs MCP server](https://docs.livekit.io/intro/mcp-server/)
- [livekit/agents](https://github.com/livekit/agents) · [livekit/livekit-cli](https://github.com/livekit/livekit-cli)
