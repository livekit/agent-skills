# Trigger eval

Checks whether a realistic request fires the right skill, and whether a near-miss fires nothing.
Atomic skills fail this way more than any other, so run it whenever a `description` changes.

```bash
python3 evals/trigger/run.py                    # Python fixture (agent-starter-python)
python3 evals/trigger/run.py --template node    # Node fixture (agent-starter-node)
```

Requires the `claude` CLI, logged in. A run takes about 12 seconds when a skill fires, and runs to
the timeout when nothing does. The skills cover both languages, so run both before releasing the set.

## The fixture and why it's safe

The harness shallow-clones a public [livekit-examples](https://github.com/livekit-examples) starter
into a temp directory, installs the repo's skills into its `.claude/skills/`, and
deletes it afterwards. It doesn't use `lk agent init` or `lk app create`, because both resolve a
LiveKit Cloud project first and write that project's credentials into the new directory. An eval
fixture must never contain credentials. `--testbed <path>` copies a local project instead, with the
same credential stripping.

Two guards keep evals from spending anything on LiveKit:

- Every `claude -p` subprocess gets dummy `LIVEKIT_URL` / `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET`
  pointing at an unroutable address. `lk` prefers the environment over its configured default
  project, so a cloud command fails instead of running against whichever project the user last
  selected.
- Tools are restricted to `Skill,Read,Glob,Grep`, so no command runs and the agent under test is
  never executed.

The deciding model is the user's Claude: whatever `claude -p` is configured with, or `--model`.
That's what's under test. LiveKit Inference isn't involved.

## Queries

`queries.json` is a list of `{"q": "...", "expect": [...]}`. `expect` lists every acceptable skill
for the request. An empty list is a near-miss that must fire nothing. Language-specific details use
placeholders filled per fixture: `{agent}` (`src/agent.py` / `src/agent.ts`), `{tests}`,
`{test_runner}` (`pytest` / `vitest`), `{sim_end_hook}`.

When adding queries, follow the platform docs: make them realistic and specific (file paths, some
backstory, casual phrasing, typos). Negative cases should share vocabulary with the skills. "Write
pytest tests for my Flask app" is a useful negative; "write a fibonacci function" isn't.

## Options and reading results

`--only 3,7,12` re-runs a subset by index. `--runs N` sets runs per query (default 2; use 3 when
confirming a fix). `--model` pins the model. `--out` sets the results JSON.

The confusion table groups queries by their acceptable set and shows what fired first. A miss
usually means a description doesn't claim a phrase users type, or two descriptions both claim it.
Fix it by having one skill's description claim the phrase and the other's disclaim it, then re-run
with `--runs 3`.

Runs only see the repo's skills (`--setting-sources project`), so this measures collisions within
the set. Users have other skills installed, so it's worth running without that flag now and then.
