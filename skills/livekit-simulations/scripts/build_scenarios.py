#!/usr/bin/env python3
"""Coverage-enforcing assembler for LiveKit simulation scenarios (no seed libraries).

This version of the skill ships NO attribute libraries — you (the coding agent) author the
scenarios from your own judgement, then this script validates them and emits the JSON shape
`lk agent simulate --config` expects. With --risks it enforces that every risk-checklist item
is covered by some scenario's `covers` ids (--strict fails the build on any gap).

Standard library only — no third-party deps, no network.

  python build_scenarios.py assemble --in authored.json \
      --agent-description-file description.md --risks risks.json --strict --out scenarios.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_risk_ids(path: Path) -> list[tuple[str, str]]:
    """Read risks.json into a list of (id, must_test) pairs. Accepts a JSON list of
    strings (ids) or objects with at least an `id` (and optional `must_test`)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("risks file must be a JSON list")
    out: list[tuple[str, str]] = []
    for item in data:
        if isinstance(item, str) and item.strip():
            out.append((item.strip(), ""))
        elif isinstance(item, dict) and str(item.get("id", "")).strip():
            out.append((str(item["id"]).strip(), str(item.get("must_test", ""))))
    return out


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
    # `covers` is accepted (it drives the coverage check) but stripped from the emitted config.
    allowed = {"label", "instructions", "agent_expectations", "metadata", "covers"}
    scenarios = []
    covered: dict[str, list[str]] = {}  # risk id -> labels of scenarios that cover it
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
        for rid in sc.get("covers") or []:
            covered.setdefault(str(rid), []).append(sc["label"])
        scenarios.append(
            {
                "label": sc["label"],
                "instructions": sc["instructions"],
                "agent_expectations": sc["agent_expectations"],
                "metadata": sc.get("metadata") or {},
            }
        )

    # Coverage enforcement against the risk checklist (optional).
    if args.risks:
        try:
            risks = load_risk_ids(Path(args.risks))
        except (OSError, json.JSONDecodeError, ValueError) as e:
            print(f"error: could not read risks file {args.risks}: {e}", file=sys.stderr)
            return 1
        risk_ids = [rid for rid, _ in risks]
        uncovered = [(rid, mt) for rid, mt in risks if rid not in covered]
        unknown_ids = sorted(c for c in covered if c not in set(risk_ids))
        print(f"coverage: {len(risk_ids) - len(uncovered)}/{len(risk_ids)} risk-checklist items covered")
        if unknown_ids:
            print(f"warning: 'covers' referenced unknown risk id(s): {', '.join(unknown_ids)}", file=sys.stderr)
        if uncovered:
            print("UNCOVERED risks (write a dedicated scenario for each):", file=sys.stderr)
            for rid, mt in uncovered:
                print(f"  - {rid}{(': ' + mt) if mt else ''}", file=sys.stderr)
            if args.strict:
                print("error: --strict set and not every risk is covered; no config written.", file=sys.stderr)
                return 1

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

    a = sub.add_parser("assemble", help="validate authored scenarios -> lk --config json")
    a.add_argument("--in", dest="infile", required=True, help="authored scenarios JSON (list)")
    a.add_argument("--agent-description-file", default="", help="markdown file with the agent description")
    a.add_argument("--risks", default="", help="risks.json checklist to enforce coverage against (via scenario 'covers' ids)")
    a.add_argument("--strict", action="store_true", help="fail (no config written) if any --risks item is uncovered")
    a.add_argument("--out", default="scenarios.json", help="output config path")
    a.set_defaults(func=cmd_assemble)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
