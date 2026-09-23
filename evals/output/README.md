# Output eval

Answers: *does following the skill produce better work than not following it?*

Method: for each of at least three realistic prompts, run two fresh agents against a testbed
project — one told to read and follow the skill, one not — and grade what they produce. Save each
run's outputs under `workspace/<iteration>/<eval-name>/{with_skill,without_skill}/outputs/`.

Build the testbed the same way the trigger harness does — a shallow `git clone` of
`livekit-examples/agent-starter-python` or `agent-starter-node` with every `.env*` removed — never
`lk agent init`, which writes a real project's credentials into the directory.

Output-eval agents need write tools, so the fixture can't stop them running commands. Two guards:

- Give the agents dummy `LIVEKIT_URL` / `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` in their
  environment (an unroutable address). `lk` and the SDKs honour environment over the user's default
  project, so an accidental `pytest`, `lk agent debugger`, or `lk agent simulate` fails instead of
  spending the project's inference or uploading source.
- Say it in the prompt anyway: outputs go to the eval workspace, not the testbed; **do not run
  `lk agent simulate` without a scenario file** — agents following the scenario skill will
  otherwise try to generate a baseline, which uploads source.

Where the LLM runs: the eval agents are the user's Claude. LiveKit Inference is only reached if an
agent executes the agent under test, which the guards above prevent.

`grade_scenarios.py <outputs-dir> --agent <src/agent.py|src/agent.ts>` grades the scenario files a
run produced, in two layers:

- **Structural, exact.** YAML parses; keys match the CLI's scenario-file struct; required fields
  present; every file has a group name; labels unique; output supports a quick/full split (several
  files or tags). Regex and dict lookups are the right tool here — these are string properties.
- **Judged, by an LLM.** One `claude -p` call (no tools) reads the agent's source and the scenario
  files and returns a verdict with quoted evidence for each of: every constraint in the agent's
  instructions is actually exercised; refusal scenarios treat the refusal as the pass; no scenario
  requires a capability the agent lacks; no date will rot; every expectation is decidable from a
  transcript; the simulated user never plays the agent's role. These are judgment calls and a keyword
  heuristic gets them wrong — an earlier version of this grader false-negatived on `"Never
  characterizes this user's headache as probably nothing"` because it wasn't in a refusal word list.

The judge derives the agent's capabilities and guardrails from the source you pass, so it works for
either starter template (and for real agents). It is the user's Claude, run with `--tools ""`, so it
can't execute anything; it costs one short call per graded output. Verdicts vary a little between
runs — pass `--judge-runs 2` or `3` for a majority, and read the evidence rather than counting
passes. `--no-judge` runs the structural layer alone; `--json` emits the full report; `--strict`
exits non-zero on any failure. Requires PyYAML (`pip install pyyaml`) and the `claude` CLI logged in.

Known confound: the starter project ships a `scenarios.yaml` that already uses the instructions
template the skill teaches, plus a CI workflow. A baseline agent copies it and looks nearly as good
as the skill run. A testbed without an exemplar file discriminates better.
