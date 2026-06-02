#!/usr/bin/env python3
"""Deterministic helpers for generating LiveKit simulation scenarios locally.

This script does ONLY the mechanical, repetition-prone parts of scenario
generation; the coding agent (you) does the judgement parts (reading the
agent's code, writing the agent description, and authoring each scenario).

Standard library only — no third-party deps, no network, no API keys — so it
runs in any project. The model work is done by the coding agent itself.

Two subcommands:

  sample    Sample N diverse "attribute sets" from the bundled libraries
            (persona / trait / emotion / situation / goal / complexity, plus
            an adversarial challenge on some fraction). Writes a worksheet
            JSON. You then author ONE scenario per slot, grounded in the
            agent's real capabilities + the user's test focus.

  assemble  Validate authored scenarios and emit a scenarios.json in the
            shape `lk agent simulate --config` expects.

Typical flow (see SKILL.md):
  python build_scenarios.py sample --count 12 --challenge-ratio 0.3 --out worksheet.json
  # ...you author one scenario per slot into authored.json...
  python build_scenarios.py assemble --in authored.json \
      --agent-description-file description.md --out scenarios.json
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

# Attribute libraries live next to this script, under ../assets/attributes/.
DEFAULT_ATTR_DIR = Path(__file__).resolve().parent.parent / "assets" / "attributes"

# 20% of slots get an open-ended goal so generation isn't boxed in (mirrors the
# source service's sampling).
OPEN_GOAL = "any realistic interaction this agent supports"


def load_library(path: Path) -> list[str]:
    """Read a `description | id` library file into a list of descriptions.

    Lines starting with `#` and blank lines are ignored. The id (after `|`) is
    only an organizational aid in the source files; we sample on description.
    """
    items: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        desc = line.split("|", 1)[0].strip()
        if desc:
            items.append(desc)
    return items


def cmd_sample(args: argparse.Namespace) -> int:
    attr_dir = Path(args.attributes_dir)
    needed = ["personas", "emotions", "situations", "goals", "challenges", "traits", "complexity"]
    libs: dict[str, list[str]] = {}
    for name in needed:
        path = attr_dir / f"{name}.txt"
        if not path.exists():
            print(f"error: missing attribute library: {path}", file=sys.stderr)
            return 1
        libs[name] = load_library(path)
        if not libs[name]:
            print(f"error: empty attribute library: {path}", file=sys.stderr)
            return 1

    rng = random.Random(args.seed)
    slots = []
    for i in range(args.count):
        goal = rng.choice(libs["goals"]) if rng.random() < 0.8 else OPEN_GOAL
        challenge = rng.choice(libs["challenges"]) if rng.random() < args.challenge_ratio else None
        slots.append(
            {
                "id": f"s{i + 1:02d}",
                "persona": rng.choice(libs["personas"]),
                "trait": rng.choice(libs["traits"]),
                "emotion": rng.choice(libs["emotions"]),
                "situation": rng.choice(libs["situations"]),
                "goal_seed": goal,
                "complexity": rng.choice(libs["complexity"]),
                "challenge": challenge,
            }
        )

    worksheet = {
        "count": args.count,
        "challenge_ratio": args.challenge_ratio,
        "seed": args.seed,
        "test_focus": args.focus or "",
        "slots": slots,
        "_note": (
            "Author ONE scenario per slot. Use the attributes as a CHARACTER SEED "
            "(personality/mood/context) and the goal_seed as a DIRECTION — ground "
            "every goal in what the agent actually supports per the description, and "
            "incorporate test_focus. Many goal_seeds will be off-domain for a specialized "
            "agent (the libraries are general) — that is expected; replace them freely. The "
            "character seed is the real signal; goal_seed is just a nudge. Drop or re-roll any "
            "slot that cannot map to a real interaction with this agent. Output authored.json: "
            "a list of {label, instructions, agent_expectations, metadata?}."
        ),
    }
    Path(args.out).write_text(json.dumps(worksheet, indent=2), encoding="utf-8")
    print(f"wrote {len(slots)} attribute slots -> {args.out}")
    if args.focus:
        print(f"test focus: {args.focus}")
    return 0


def cmd_assemble(args: argparse.Namespace) -> int:
    try:
        authored = json.loads(Path(args.infile).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"error: could not read {args.infile}: {e}", file=sys.stderr)
        return 1
    if isinstance(authored, dict) and "scenarios" in authored:
        authored = authored["scenarios"]
    if not isinstance(authored, list) or not authored:
        print("error: authored input must be a non-empty list of scenarios", file=sys.stderr)
        return 1

    agent_description = ""
    if args.agent_description_file:
        agent_description = Path(args.agent_description_file).read_text(encoding="utf-8").strip()

    required = ("label", "instructions", "agent_expectations")
    allowed = {"label", "instructions", "agent_expectations", "metadata"}
    scenarios = []
    for idx, sc in enumerate(authored):
        missing = [f for f in required if not str(sc.get(f, "")).strip()]
        if missing:
            print(f"error: scenario #{idx + 1} missing/empty fields: {', '.join(missing)}", file=sys.stderr)
            return 1
        unknown = [k for k in sc if k not in allowed]
        if unknown:
            print(
                f"warning: scenario #{idx + 1} ({sc['label']!r}) has unrecognized key(s) that will "
                f"be DROPPED: {', '.join(unknown)} — expected one of {sorted(allowed)} "
                f"(e.g. 'agent_expectations', not 'expectations').",
                file=sys.stderr,
            )
        scenarios.append(
            {
                "label": sc["label"],
                "instructions": sc["instructions"],
                "agent_expectations": sc["agent_expectations"],
                "metadata": sc.get("metadata") or {},
            }
        )

    config = {"agent_description": agent_description, "scenarios": scenarios}
    Path(args.out).write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"wrote {len(scenarios)} scenarios -> {args.out}")
    print(
        "reminder: skim each agent_expectations against the agent description — an expectation "
        "that requires the agent to do something it cannot do (or should refuse) is a bad test."
    )
    print(f"run: lk agent simulate --config {args.out}   # confirm exact flags with --help")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    s = sub.add_parser("sample", help="sample N attribute sets into a worksheet")
    s.add_argument("--count", type=int, default=20, help="number of scenarios to seed (default: 20)")
    s.add_argument("--challenge-ratio", type=float, default=0.3,
                   help="fraction of slots that get an adversarial challenge (default: 0.3)")
    s.add_argument("--focus", default="", help="free-text test focus to thread into authoring")
    s.add_argument("--attributes-dir", default=str(DEFAULT_ATTR_DIR),
                   help="dir of attribute libraries (default: bundled)")
    s.add_argument("--seed", type=int, default=0, help="random seed for reproducible sampling")
    s.add_argument("--out", default="worksheet.json", help="output worksheet path")
    s.set_defaults(func=cmd_sample)

    a = sub.add_parser("assemble", help="validate authored scenarios -> lk --config json")
    a.add_argument("--in", dest="infile", required=True, help="authored scenarios JSON (list)")
    a.add_argument("--agent-description-file", default="", help="markdown file with the agent description")
    a.add_argument("--out", default="scenarios.json", help="output config path")
    a.set_defaults(func=cmd_assemble)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
