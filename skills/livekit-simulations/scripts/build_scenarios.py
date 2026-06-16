#!/usr/bin/env python3
"""Coverage-enforcing assembler for LiveKit simulation scenarios (no seed libraries).

This version of the skill ships NO attribute libraries — you (the coding agent) author the
scenarios from your own judgement, then this script validates them and emits the YAML scenarios
file `lk agent simulate --scenarios` expects. With --risks it enforces that every risk-checklist
item is covered by some scenario's `covers` ids (--strict fails the build on any gap).

The produced scenarios file is ALWAYS YAML — that is the format `--scenarios` loads.

Standard library only — no third-party deps, no network.

  python build_scenarios.py assemble --in authored.yaml \
      --agent-description-file description.md --risks risks.yaml --strict --out scenarios.yaml
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _yaml_scalar(v) -> str:
    """Encode a scalar as a valid YAML node. A JSON string literal is also a valid YAML
    double-quoted scalar, so json.dumps gives us correct escaping (quotes, backslashes,
    newlines, control chars) for free — and YAML accepts raw UTF-8 in double quotes."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, (int, float)):
        return json.dumps(v)
    return json.dumps(str(v), ensure_ascii=False)


def to_yaml(data, indent: int = 0) -> list[str]:
    """Emit block-style YAML for the dict/list/scalar shapes this script produces."""
    pad = "  " * indent
    lines: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                if not value:
                    lines.append(f"{pad}{key}: {{}}")
                else:
                    lines.append(f"{pad}{key}:")
                    lines.extend(to_yaml(value, indent + 1))
            elif isinstance(value, list):
                if not value:
                    lines.append(f"{pad}{key}: []")
                else:
                    lines.append(f"{pad}{key}:")
                    lines.extend(to_yaml(value, indent + 1))
            else:
                lines.append(f"{pad}{key}: {_yaml_scalar(value)}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item:
                inner = to_yaml(item, indent + 1)
                # Hoist the first key onto the "- " marker line; the rest align under it.
                lines.append(f"{pad}- {inner[0].lstrip()}")
                lines.extend(inner[1:])
            elif isinstance(item, (dict, list)):
                lines.append(f"{pad}- {{}}" if isinstance(item, dict) else f"{pad}- []")
            else:
                lines.append(f"{pad}- {_yaml_scalar(item)}")
    return lines


# --------------------------------------------------------------------------------------------
# YAML reader. Inputs (authored.yaml, risks.yaml) are YAML. The stdlib has no YAML parser and we
# keep the "no third-party deps" promise, so this is a compact reader for the block-style subset
# the skill documents: sequences, mappings, plain/quoted scalars, flow [..]/{..}, and `|`/`>`
# block scalars. JSON is valid YAML, so a JSON fast-path handles JSON inputs bulletproofly.
# --------------------------------------------------------------------------------------------

_BLOCK_RE = re.compile(r"^[|>][+-]?\d*$")  # block-scalar indicator: |, >, |-, >+, |2, ...
_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(r"^[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?$")


def _coerce_plain(text: str):
    low = text.lower()
    if low in ("", "null", "~"):
        return None
    if low == "true":
        return True
    if low == "false":
        return False
    if _INT_RE.match(text):
        return int(text)
    if _FLOAT_RE.match(text) and any(c in text for c in ".eE"):
        return float(text)
    return text


def _split_flow(body: str) -> list[str]:
    """Split a flow-collection body on top-level commas, respecting quotes and nesting."""
    items, buf, depth, quote, i = [], [], 0, None, 0
    while i < len(body):
        ch = body[i]
        if quote:
            buf.append(ch)
            if ch == "\\" and quote == '"' and i + 1 < len(body):
                buf.append(body[i + 1]); i += 2; continue
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch; buf.append(ch)
        elif ch in "[{":
            depth += 1; buf.append(ch)
        elif ch in "]}":
            depth -= 1; buf.append(ch)
        elif ch == "," and depth == 0:
            items.append("".join(buf).strip()); buf = []
        else:
            buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        items.append(tail)
    return items


def _parse_scalar(text: str):
    """Parse a single inline node: quoted/plain scalar or flow collection."""
    if text == "":
        return None
    c = text[0]
    if c == '"':
        return json.loads(text)  # a JSON string literal is a valid YAML double-quoted scalar
    if c == "'":
        inner = text[1:-1] if len(text) >= 2 and text.endswith("'") else text[1:]
        return inner.replace("''", "'")
    if c == "[":
        return [_parse_scalar(tok) for tok in _split_flow(text[1:-1].strip())]
    if c == "{":
        out = {}
        for pair in _split_flow(text[1:-1].strip()):
            k, _, v = pair.partition(":")
            out[str(_parse_scalar(k.strip()))] = _parse_scalar(v.strip())
        return out
    return _coerce_plain(text)


class _YamlReader:
    """Recursive-descent reader for the documented block-YAML subset."""

    def __init__(self, text: str):
        self.lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        self.n = len(self.lines)
        self.i = 0

    @staticmethod
    def _indent(line: str) -> int:
        return len(line) - len(line.lstrip(" "))

    def _skip(self) -> None:
        while self.i < self.n:
            s = self.lines[self.i].strip()
            if s == "" or s.startswith("#"):
                self.i += 1
            else:
                break

    def _peek(self):
        self._skip()
        if self.i >= self.n:
            return None
        line = self.lines[self.i]
        return self._indent(line), line.strip()

    def parse(self):
        p = self._peek()
        if p is None:
            return None
        return self._sequence(p[0]) if self._is_seq(p[1]) else self._mapping(p[0])

    @staticmethod
    def _is_seq(content: str) -> bool:
        return content == "-" or content.startswith("- ")

    @staticmethod
    def _is_mapping_start(rest: str) -> bool:
        depth, quote, i = 0, None, 0
        while i < len(rest):
            ch = rest[i]
            if quote:
                if ch == "\\" and quote == '"':
                    i += 2; continue
                if ch == quote:
                    quote = None
            elif ch in ('"', "'"):
                quote = ch
            elif ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1
            elif ch == ":" and depth == 0 and (i + 1 == len(rest) or rest[i + 1] == " "):
                return True
            i += 1
        return False

    def _split_key_val(self, content: str):
        if content[0] in ('"', "'"):
            q, j = content[0], 1
            while j < len(content):
                if content[j] == "\\" and q == '"':
                    j += 2; continue
                if content[j] == q:
                    break
                j += 1
            key = str(_parse_scalar(content[: j + 1]))
            rest = content[j + 1 :]
            colon = rest.find(":")
            return key, (rest[colon + 1 :].strip() if colon >= 0 else "")
        colon = content.find(":")
        if colon < 0:
            return content.strip(), ""
        return content[:colon].strip(), content[colon + 1 :].strip()

    def _block_value(self, parent_indent: int):
        p = self._peek()
        if p is None:
            return None
        actual, content = p
        if self._is_seq(content):
            return self._sequence(actual) if actual >= parent_indent else None
        return self._mapping(actual) if actual > parent_indent else None

    def _value(self, val: str, key_indent: int):
        if val == "":
            return self._block_value(key_indent)
        if _BLOCK_RE.match(val):
            return self._block_scalar(val, key_indent)
        return _parse_scalar(val)

    def _mapping(self, indent: int, seed: str | None = None):
        result: dict = {}
        if seed is not None:
            key, val = self._split_key_val(seed)
            result[key] = self._value(val, indent)
        while True:
            p = self._peek()
            if p is None or p[0] != indent or self._is_seq(p[1]):
                break
            key, val = self._split_key_val(self.lines[self.i].strip())
            self.i += 1
            result[key] = self._value(val, indent)
        return result

    def _sequence(self, indent: int):
        items: list = []
        while True:
            p = self._peek()
            if p is None or p[0] != indent or not self._is_seq(p[1]):
                break
            line = self.lines[self.i]
            self.i += 1
            content = line.strip()
            rest = content[1:].lstrip(" ")
            if rest == "":
                items.append(self._block_value(indent))
            elif self._is_mapping_start(rest):
                entry_indent = self._indent(line) + (len(content) - len(rest))
                items.append(self._mapping(entry_indent, seed=rest))
            else:
                items.append(self._value(rest, indent))
        return items

    def _block_scalar(self, marker: str, key_indent: int) -> str:
        folded = marker[0] == ">"
        chomp = next((c for c in marker[1:] if c in "+-"), "")
        collected: list[str] = []
        block_indent = None
        while self.i < self.n:
            line = self.lines[self.i]
            if line.strip() == "":
                collected.append(""); self.i += 1; continue
            ind = self._indent(line)
            if ind <= key_indent:
                break
            if block_indent is None:
                block_indent = ind
            collected.append(line[block_indent:])
            self.i += 1
        while collected and collected[-1] == "":
            collected.pop()
        if block_indent is None:
            return ""
        if folded:
            out, prev_blank = [], True
            for ln in collected:
                if ln == "":
                    out.append("\n"); prev_blank = True
                else:
                    if out and not prev_blank:
                        out.append(" ")
                    out.append(ln); prev_blank = False
            text = "".join(out)
        else:
            text = "\n".join(collected)
        if chomp == "-":
            return text.rstrip("\n")
        if chomp == "+":
            return text + "\n"
        return text + "\n" if text and not text.endswith("\n") else text


def load_structured(path: Path):
    """Load a YAML (or JSON, a YAML subset) input file into Python data."""
    text = Path(path).read_text(encoding="utf-8")
    if text.lstrip()[:1] in ("[", "{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    return _YamlReader(text).parse()


def load_risk_ids(path: Path) -> list[tuple[str, str]]:
    """Read risks.yaml into a list of (id, must_test) pairs. Accepts a YAML list of
    strings (ids) or mappings with at least an `id` (and optional `must_test`)."""
    data = load_structured(path)
    if not isinstance(data, list):
        raise ValueError("risks file must be a list")
    out: list[tuple[str, str]] = []
    for item in data:
        if isinstance(item, str) and item.strip():
            out.append((item.strip(), ""))
        elif isinstance(item, dict) and str(item.get("id", "")).strip():
            out.append((str(item["id"]).strip(), str(item.get("must_test", ""))))
    return out


def cmd_assemble(args: argparse.Namespace) -> int:
    try:
        authored = load_structured(Path(args.infile))
    except (OSError, ValueError, json.JSONDecodeError) as e:
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
    Path(args.out).write_text("\n".join(to_yaml(config)) + "\n", encoding="utf-8")
    print(f"wrote {len(scenarios)} scenarios -> {args.out}")
    print(
        "reminder: skim each agent_expectations against the agent description — an expectation "
        "that requires the agent to do something it cannot do (or should refuse) is a bad test."
    )
    print(f"run: lk agent simulate --scenarios {args.out}   # confirm exact flags with --help")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    a = sub.add_parser("assemble", help="validate authored scenarios -> lk --scenarios yaml")
    a.add_argument("--in", dest="infile", required=True, help="authored scenarios YAML (list)")
    a.add_argument("--agent-description-file", default="", help="markdown file with the agent description")
    a.add_argument("--risks", default="", help="risks.yaml checklist to enforce coverage against (via scenario 'covers' ids)")
    a.add_argument("--strict", action="store_true", help="fail (no config written) if any --risks item is uncovered")
    a.add_argument("--out", default="scenarios.yaml", help="output scenarios file path (YAML)")
    a.set_defaults(func=cmd_assemble)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
