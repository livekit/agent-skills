#!/usr/bin/env python3
"""Grade the scenario files an eval run produced for an agent.

Two layers:

  structural  Deterministic checks: YAML parses, keys match the CLI's scenario-file struct,
              required fields present, group name set, output supports a quick/full split.
              A malformed file shouldn't reach the judge.
  judged      One `claude -p` call that reads the agent's source and the scenario files and
              answers the questions that need judgment: is every constraint in the agent's
              instructions exercised, do refusal scenarios treat the refusal as the pass, does
              any scenario require a capability the agent lacks, will any date rot, is any
              expectation too vague to grade consistently. Returns per-assertion verdicts with
              quoted evidence for spot-checking.

    python3 evals/output/grade_scenarios.py <outputs-dir> --agent <path/to/src/agent.py>
    python3 evals/output/grade_scenarios.py <outputs-dir> --agent src/agent.ts --judge-runs 2

The judge is the user's Claude (whatever `claude -p` is configured with, or --model), run with no
tools so it can't execute anything. It only sees what's passed in. Verdicts vary a little between
runs; --judge-runs N takes a majority per assertion. Structural results are exact."""
import argparse, json, os, pathlib, re, subprocess, sys
from collections import Counter

# Mirrors the CLI's scenariosFile / yamlScenario structs (cmd/lk/simulate.go). Verify against the
# installed CLI if this grader starts rejecting files the CLI accepts.
FILE_KEYS = {"name", "scenarios", "id"}
SCEN_KEYS = {"label", "instructions", "agent_expectations", "tags", "userdata", "id"}
REQUIRED = ("label", "instructions", "agent_expectations")

JUDGE_ASSERTIONS = {
    "covers_every_constraint":
        "For every guardrail, refusal rule, or hard limit stated in the agent's instructions, at least one "
        "scenario has the simulated user actually attempt the thing (not merely mention the topic).",
    "refusals_are_the_pass":
        "In every scenario where the simulated user requests something the agent should decline, deflect, or "
        "not fabricate, agent_expectations treats that refusal or honest limit as the passing outcome.",
    "no_invented_capabilities":
        "No scenario's passing outcome requires the agent to perform an action it has no tool or ability for "
        "(look at what the agent's code actually implements — e.g. an agent with no function tools cannot "
        "book, look up, send, or transfer). Asking for such an action and expecting a refusal is fine.",
    "no_rotting_dates":
        "No scenario depends on a relative date ('tomorrow', 'next week') or an implicit current date that "
        "would change the expected outcome months from now.",
    "expectations_are_decidable":
        "Every agent_expectations is specific enough that a judge reading only the transcript could decide "
        "pass or fail consistently — outcomes, not wording; no expectation that swings on interpretation.",
    "no_agent_role_confusion":
        "In every scenario the simulated user speaks TO the agent; no scenario has the simulated user "
        "performing the agent's own duties (greeting the caller, processing the order).",
}

def load_scenario_files(d: pathlib.Path):
    import yaml
    files, aux = [], []
    for p in sorted(d.rglob("*.y*ml")):
        try: y = yaml.safe_load(p.read_text())
        except Exception as e:
            files.append((p, {"__parse_error__": str(e)})); continue
        (files if isinstance(y, dict) and isinstance(y.get("scenarios"), list) else aux).append((p, y))
    return files, [p.name for p, _ in aux]

def structural(files, aux):
    res, ev = {}, {}
    parsed = [(p, y) for p, y in files if "__parse_error__" not in y]
    res["produces_parseable_scenario_yaml"] = bool(parsed) and len(parsed) == len(files)
    ev["produces_parseable_scenario_yaml"] = f"{len(parsed)} scenario file(s) {[p.name for p,_ in parsed]}; auxiliary (ungraded): {aux or 'none'}; parse errors: {[p.name for p,y in files if '__parse_error__' in y] or 'none'}"
    scen, bad_keys, missing = [], [], []
    for p, y in parsed:
        bad_keys += [f"{p.name}:{k}" for k in y if k not in FILE_KEYS]
        for s in y["scenarios"]:
            if not isinstance(s, dict): continue
            scen.append(s)
            bad_keys += [f"{p.name}:{k}" for k in s if k not in SCEN_KEYS]
            missing += [f"{p.name}:{s.get('label','?')}:{k}" for k in REQUIRED if not s.get(k)]
    res["schema_matches_cli_struct"] = not bad_keys
    ev["schema_matches_cli_struct"] = f"unknown keys: {sorted(set(bad_keys)) or 'none'}"
    res["required_fields_present"] = bool(scen) and not missing
    ev["required_fields_present"] = f"{len(scen)} scenarios; missing: {sorted(set(missing)) or 'none'}"
    res["every_file_has_group_name"] = bool(parsed) and all(y.get("name") for _, y in parsed)
    ev["every_file_has_group_name"] = f"names: {[y.get('name') for _, y in parsed]}"
    has_tags = any(s.get("tags") for s in scen)
    res["supports_quick_vs_full_split"] = len(parsed) > 1 or has_tags
    ev["supports_quick_vs_full_split"] = f"{len(parsed)} file(s); tags used: {has_tags}"
    labels = [s.get("label") for s in scen]
    res["labels_unique"] = len(labels) == len(set(labels))
    ev["labels_unique"] = f"duplicates: {[l for l, c in Counter(labels).items() if c > 1] or 'none'}"
    return res, ev, len(scen)

def judge_once(agent_src: str, scenario_text: str, model: str | None, timeout: int) -> dict:
    schema = {k: {"passed": "true|false", "evidence": "1-3 short quotes or scenario labels that justify the verdict"} for k in JUDGE_ASSERTIONS}
    prompt = f"""You are grading a set of simulation scenarios written to test a LiveKit voice agent. A scenario is a simulated user's `instructions` (persona and goals) plus `agent_expectations` (what the judge grades the transcript against). Your job is to decide, for each assertion below, whether the scenario set satisfies it, with evidence.

Read the agent's source first and derive from it: what the agent CAN do (its tools, if any — note whether any function tools are actually registered or only present as comments), and every constraint, guardrail, or refusal rule in its instructions.

## Assertions
{json.dumps(JUDGE_ASSERTIONS, indent=2)}

## Agent source
```
{agent_src}
```

## Scenario files
{scenario_text}

Respond with ONLY a JSON object, no prose before or after, exactly this shape (booleans, not strings):
{json.dumps(schema, indent=2)}"""
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--tools", "", "--no-session-persistence", "--setting-sources", "project"]
    if model: cmd += ["--model", model]
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env, cwd=os.path.dirname(os.path.abspath(__file__)))
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"judge call exceeded {timeout}s — large scenario sets take longer; raise --timeout") from None
    text = out.stdout.strip()
    try: text = json.loads(text).get("result", text)
    except Exception: pass
    m = re.search(r"\{.*\}", text, re.S)
    if not m: raise RuntimeError(f"judge returned no JSON (rc={out.returncode}): {text[:300]!r}")
    verdicts = json.loads(m.group(0))
    return {k: {"passed": bool(v.get("passed")) if isinstance(v, dict) else bool(v),
                "evidence": (v.get("evidence") if isinstance(v, dict) else "")} for k, v in verdicts.items() if k in JUDGE_ASSERTIONS}

def judged(agent_path: pathlib.Path, files, model, runs, timeout):
    agent_src = agent_path.read_text()
    scenario_text = "\n\n".join(f"### {p.name}\n```yaml\n{p.read_text()}\n```" for p, y in files if "__parse_error__" not in y)
    votes = {k: [] for k in JUDGE_ASSERTIONS}; evidence = {k: [] for k in JUDGE_ASSERTIONS}
    for _ in range(runs):
        v = judge_once(agent_src, scenario_text, model, timeout)
        for k in JUDGE_ASSERTIONS:
            if k in v: votes[k].append(v[k]["passed"]); evidence[k].append(v[k]["evidence"])
    res = {k: (sum(votes[k]) * 2 > len(votes[k])) if votes[k] else None for k in JUDGE_ASSERTIONS}
    ev = {k: (f"votes {sum(votes[k])}/{len(votes[k])} pass; " + str(evidence[k][-1] if evidence[k] else "")) for k in JUDGE_ASSERTIONS}
    return res, ev

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outputs", help="directory containing the produced scenario file(s)")
    ap.add_argument("--agent", required=True, help="the agent source the scenarios were written for (src/agent.py or src/agent.ts)")
    ap.add_argument("--judge-runs", type=int, default=1, help="judge calls; majority per assertion")
    ap.add_argument("--model", default=None, help="model for the judge (default: your configured claude -p model)")
    ap.add_argument("--timeout", type=int, default=300, help="seconds per judge call; large scenario sets need more")
    ap.add_argument("--no-judge", action="store_true", help="structural checks only")
    ap.add_argument("--json", action="store_true", help="print full JSON instead of a summary")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any check fails")
    a = ap.parse_args()

    d = pathlib.Path(a.outputs); files, aux = load_scenario_files(d)
    s_res, s_ev, n = structural(files, aux)
    j_res, j_ev = ({}, {})
    if not a.no_judge and s_res["produces_parseable_scenario_yaml"]:
        j_res, j_ev = judged(pathlib.Path(a.agent).expanduser(), files, a.model, a.judge_runs, a.timeout)
    report = {"outputs": str(d), "agent": a.agent, "scenario_count": n,
              "structural": {k: {"passed": v, "evidence": s_ev[k]} for k, v in s_res.items()},
              "judged": {k: {"passed": v, "evidence": j_ev[k]} for k, v in j_res.items()}}
    if a.json: print(json.dumps(report, indent=2))
    else:
        print(f"{d}  ({n} scenarios)")
        print("structural (exact):")
        for k, v in s_res.items(): print(f"  {'PASS' if v else 'FAIL'}  {k:36} {s_ev[k][:110]}")
        if j_res:
            print("judged (LLM, read the evidence):")
            for k, v in j_res.items(): print(f"  {'PASS' if v else 'FAIL' if v is not None else '  ? '}  {k:36} {str(j_ev[k])[:160]}")
    failed = [k for k, v in {**s_res, **j_res}.items() if v is False]
    sys.exit(1 if (a.strict and failed) else 0)

if __name__ == "__main__":
    main()
