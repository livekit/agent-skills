# Trigger eval

Answers: *given a realistic request, does the right skill fire — and does nothing fire for a
near-miss?* This is the failure mode a set of atomic skills is most exposed to, so run it whenever a
`description` changes.

```bash
python3 evals/trigger/run.py                    # Python fixture (agent-starter-python)
python3 evals/trigger/run.py --template node    # Node fixture (agent-starter-node)
```

Requires the `claude` CLI, logged in. About 12 seconds per triggered run, up to the timeout when
nothing fires. Skills are meant to work for both languages, so run both before a release of the set.

## The fixture, and why it's safe

The harness shallow-clones a public [livekit-examples](https://github.com/livekit-examples) starter
into a temp directory, deletes it afterwards, and installs the repo's non-deprecated skills into its
`.claude/skills/`. It does **not** use `lk agent init` or `lk app create`: both resolve a LiveKit
Cloud project first and write that project's credentials into the new directory, which is the one
thing an eval fixture must never contain. `--testbed <path>` copies a local project instead, with
the same credential stripping.

Two guards keep evals from spending anything on LiveKit:

- Every `claude -p` subprocess gets dummy `LIVEKIT_URL` / `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET`
  pointing at an unroutable address. `lk` honours environment over its configured default project,
  so a cloud command would fail rather than run against whichever project the user last selected.
- Tools are restricted to `Skill,Read,Glob,Grep`, so the agent under test is never executed and no
  command runs at all.

**Where the LLM runs:** the deciding model is the user's Claude — whatever `claude -p` is configured
with, or `--model`. That's the thing under test. LiveKit Inference is not involved.

## Queries

`queries.json` is a list of `{"q": "...", "expect": [...]}`. `expect` lists every acceptable skill
for that request; an empty list means a near-miss that must fire nothing. Language-specific details
use placeholders filled per fixture: `{agent}` (`src/agent.py` / `src/agent.ts`), `{tests}`,
`{test_runner}` (`pytest` / `vitest`), `{sim_end_hook}`.

Guidelines for adding queries, from the platform docs: realistic and specific (file paths, a bit of
backstory, casual phrasing, typos), not abstract; and the should-not-trigger cases should share
vocabulary with the skills — "write pytest tests for my Flask app" is a useful negative, "write a
fibonacci function" is not.

## Options and reading results

`--only 3,7,12` re-runs a subset by index; `--runs N` per query (default 2; use 3 when confirming a
fix); `--model` pins the model; `--out` sets the results JSON.

The confusion table groups queries by their acceptable set and shows what fired first. A miss is
either a description that doesn't claim a phrase users actually type, or two descriptions that both
claim it — fix by making one skill's description claim it and the other's disclaim it, then re-run
with `--runs 3`.

Only the repo's skills are visible to the runs (`--setting-sources project`), so this measures
collisions within the set. Users have other skills installed; an occasional run without that flag
is worth doing.
