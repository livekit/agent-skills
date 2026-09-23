#!/usr/bin/env python3
"""Trigger-collision harness.

Builds a throwaway fixture project, installs every skill from skills/ into it, runs
each query in queries.json through `claude -p`, and records which skill fired first. Each query
lists its acceptable skill(s) under "expect". An empty list means nothing should fire.

    python3 evals/trigger/run.py                       # fixture: agent-starter-python, cloned
    python3 evals/trigger/run.py --template node       # fixture: agent-starter-node
    python3 evals/trigger/run.py --testbed ../some-agent-project
    python3 evals/trigger/run.py --only 17,18,19 --runs 3

The fixture is a shallow `git clone` of a public livekit-examples template. It doesn't use
`lk agent init` or `lk app create`, since both resolve a LiveKit Cloud project first and write its
credentials into the new directory. Any `.env*` files are removed from the fixture, and every
`claude -p` subprocess gets dummy LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET pointing at an
unroutable address. `lk` prefers those over the user's configured default project, so an agent
that ignored instructions and ran a cloud command would fail without spending anything.

The deciding model is the user's Claude (whatever `claude -p` is configured with, or --model).
LiveKit Inference isn't involved: tools are read-only, so the agent under test never runs.
"""
import argparse, json, os, re, select, shutil, subprocess, sys, tempfile, time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SKILLS_DIR = os.path.join(ROOT, "skills")

TEMPLATES = {
    "python": {"repo": "https://github.com/livekit-examples/agent-starter-python",
               "agent": "src/agent.py", "tests": "tests/test_agent.py", "test_runner": "pytest",
               "sim_end_hook": "on_simulation_end"},
    "node":   {"repo": "https://github.com/livekit-examples/agent-starter-node",
               "agent": "src/agent.ts", "tests": "src/agent.test.ts", "test_runner": "vitest",
               "sim_end_hook": "onSimulationEnd"},
}
# Credentials that can't reach any LiveKit project. They override the user's default `lk` project.
SAFE_ENV = {"LIVEKIT_URL": "http://127.0.0.1:1", "LIVEKIT_API_KEY": "eval-dummy-key",
            "LIVEKIT_API_SECRET": "eval-dummy-secret-eval-dummy-secret-eval"}

def build_fixture(template: str | None, testbed: str | None) -> tuple[str, list[str], dict]:
    proj = tempfile.mkdtemp(prefix="skill-trigger-eval-")
    if testbed:
        for item in os.listdir(testbed):
            if item in (".git", "node_modules", ".venv", ".uv-cache", "__pycache__"): continue
            src = os.path.join(testbed, item); dst = os.path.join(proj, item)
            shutil.copytree(src, dst) if os.path.isdir(src) else shutil.copy(src, dst)
        vars_ = TEMPLATES["node" if os.path.exists(os.path.join(proj, "package.json")) else "python"]
    else:
        subprocess.run(["git", "clone", "--depth", "1", "--quiet", TEMPLATES[template]["repo"], proj], check=True)
        vars_ = TEMPLATES[template]
    # never carry credentials into the fixture
    for root, _, files in os.walk(proj):
        for f in files:
            if f.startswith(".env"): os.remove(os.path.join(root, f))
    shutil.rmtree(os.path.join(proj, ".git"), ignore_errors=True)
    # the template ships its own .claude/ (skills, settings); replace it with just ours
    shutil.rmtree(os.path.join(proj, ".claude"), ignore_errors=True)
    dst = os.path.join(proj, ".claude", "skills"); os.makedirs(dst)
    skills = []
    for name in sorted(os.listdir(SKILLS_DIR)):
        md = os.path.join(SKILLS_DIR, name, "SKILL.md")
        if not os.path.isfile(md): continue
        shutil.copytree(os.path.join(SKILLS_DIR, name), os.path.join(dst, name)); skills.append(name)
    subprocess.run(["git", "init", "-q"], cwd=proj, check=False)
    return proj, skills, vars_

def fill(q: str, vars_: dict) -> str:
    for k, v in vars_.items():
        if k != "repo": q = q.replace("{" + k + "}", v)
    return q

def run_query(q: str, proj: str, skills: list, model: str | None, timeout: int):
    cmd = ["claude", "-p", q, "--output-format", "stream-json", "--verbose", "--include-partial-messages",
           "--no-session-persistence", "--setting-sources", "project", "--tools", "Skill,Read,Glob,Grep"]
    if model: cmd += ["--model", model]
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}; env.update(SAFE_ENV)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, cwd=proj, env=env)
    fired, buf, t0, saw_json = [], "", time.time(), False
    def scan(line: str):
        nonlocal saw_json
        if line.startswith("{"): saw_json = True
        try: ev = json.loads(line)
        except Exception: return
        if ev.get("type") != "assistant": return
        for c in ev.get("message", {}).get("content", []):
            if c.get("type") != "tool_use": continue
            inp = c.get("input", {}) or {}
            if c.get("name") == "Skill":
                for k in skills:
                    if k in str(inp.get("skill", "")): fired.append(k)
            elif c.get("name") == "Read":
                m = re.search(r"\.claude/skills/([a-z0-9-]+)/", str(inp.get("file_path", "")))
                if m and m.group(1) in skills: fired.append(m.group(1))
    try:
        while time.time() - t0 < timeout and not fired:
            if p.poll() is not None:
                buf += (p.stdout.read() or b"").decode("utf-8", "replace")
                for line in buf.splitlines(): scan(line)
                break
            r, _, _ = select.select([p.stdout], [], [], 1.0)
            if not r: continue
            chunk = os.read(p.stdout.fileno(), 65536)
            if not chunk: break
            buf += chunk.decode("utf-8", "replace")
            while "\n" in buf:
                line, buf = buf.split("\n", 1); scan(line)
        if not saw_json and not fired:
            print(f"!! no stream-json from claude (rc={p.poll()}) — bad flag or not logged in?", file=sys.stderr, flush=True)
    finally:
        if p.poll() is None: p.kill(); p.wait()
    return (fired[0] if fired else None), round(time.time() - t0, 1)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    fx = ap.add_mutually_exclusive_group()
    fx.add_argument("--template", choices=sorted(TEMPLATES), default="python", help="livekit-examples starter to clone as the fixture")
    fx.add_argument("--testbed", help="a local agent project to copy instead (credentials are stripped)")
    ap.add_argument("--queries", default=os.path.join(HERE, "queries.json"))
    ap.add_argument("--only", help="comma-separated query indices")
    ap.add_argument("--runs", type=int, default=2, help="runs per query (use 3 when confirming a fix)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--timeout", type=int, default=90, help="seconds per run")
    ap.add_argument("--model", default=None, help="model for claude -p (default: your configured model)")
    ap.add_argument("--out", default=os.path.join(HERE, "results.json"))
    a = ap.parse_args()

    evals = json.load(open(a.queries))
    idx = [int(x) for x in a.only.split(",")] if a.only else list(range(len(evals)))
    proj, skills, vars_ = build_fixture(None if a.testbed else a.template, os.path.expanduser(a.testbed) if a.testbed else None)
    print(f"fixture: {proj}\nskills under test: {skills}\n", file=sys.stderr)
    try:
        results = defaultdict(list)
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            futs = {ex.submit(run_query, fill(evals[i]["q"], vars_), proj, skills, a.model, a.timeout): i
                    for i in idx for _ in range(a.runs)}
            for f in as_completed(futs):
                i = futs[f]; first, dt = f.result(); results[i].append(first)
                print(f"[{i:02d}] {dt:5.1f}s fired={first or '-':32} expect={evals[i]['expect'] or ['none']}", file=sys.stderr, flush=True)
    finally:
        shutil.rmtree(proj, ignore_errors=True)

    rows, table, passed, total = [], defaultdict(Counter), 0, 0
    for i in idx:
        exp = set(evals[i]["expect"]); ok = 0
        for first in results[i]:
            ok += (first is None) if not exp else (first in exp)
            table[",".join(sorted(exp)) or "none"][first or "none"] += 1
        passed += ok; total += len(results[i])
        rows.append({"i": i, "q": fill(evals[i]["q"], vars_), "expect": sorted(exp), "fired": results[i], "pass": f"{ok}/{len(results[i])}"})
    json.dump({"fixture": a.testbed or a.template, "model": a.model, "runs": a.runs, "rows": rows}, open(a.out, "w"), indent=2)

    print(f"\n=== {passed}/{total} runs fired an acceptable skill (or none when none expected) ===")
    print("\n=== expected -> fired first ===")
    for exp, c in sorted(table.items()): print(f"{exp:62} -> {dict(c)}")
    print("\n=== misses ===")
    for r in rows:
        if r["pass"].split("/")[0] != r["pass"].split("/")[1]:
            print(f"- {r['pass']}  expect={r['expect'] or ['none']} fired={r['fired']}\n    {r['q'][:110]}")
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
