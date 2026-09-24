#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["pyyaml"]
# ///
"""Structural checks on every skills/*/SKILL.md. Exits 1 on any failure.

Covers the AGENTS.md rules that can be checked mechanically: frontmatter fields, name matches the
directory, description length and third person, body length, references exist and have a TOC when
long, cross-references resolve, no time-relative phrasing."""
import pathlib, re, sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
TIME_RELATIVE = re.compile(r"\b(newer CLIs?|as of writing|is landing|are landing|still moving|recently added|coming soon)\b", re.I)

def main() -> int:
    failures = 0
    names = {p.name for p in SKILLS.iterdir() if p.is_dir()}
    all_text = ""
    for skill_md in sorted(SKILLS.glob("*/SKILL.md")):
        text = skill_md.read_text(); all_text += text
        for ref in skill_md.parent.glob("references/*.md"): all_text += ref.read_text()
        probs = []
        parts = text.split("---\n", 2)
        if len(parts) < 3 or not text.startswith("---\n"):
            print(f"FAIL {skill_md}: no frontmatter"); failures += 1; continue
        body = parts[2]
        try:
            fm = yaml.safe_load(parts[1])
        except yaml.YAMLError as e:
            print(f"FAIL {skill_md}: frontmatter is not valid YAML: {e}"); failures += 1; continue
        name, desc = fm.get("name"), fm.get("description")
        if not name or name != skill_md.parent.name: probs.append(f"name {name!r} != directory")
        if name and (len(name) > 64 or not re.fullmatch(r"[a-z0-9-]+", name) or re.search(r"claude|anthropic", name)): probs.append("name violates format")
        if not desc: probs.append("missing description")
        else:
            if len(desc) > 1024: probs.append(f"description {len(desc)} chars > 1024")
            if not re.match(r"^[A-Z][a-z]+s\b", desc): probs.append("description not third person (should open like 'Runs …')")
        if not fm.get("license"): probs.append("missing license")
        meta = fm.get("metadata") or {}
        if not meta.get("author") or not isinstance(meta.get("version"), str): probs.append("missing metadata.author/version")
        if len(body.splitlines()) > 500: probs.append(f"body {len(body.splitlines())} lines > 500")
        for ref in set(re.findall(r"references/([A-Za-z0-9_-]+\.md)", body)):
            rp = skill_md.parent / "references" / ref
            if not rp.exists(): probs.append(f"missing {ref}")
            elif len(rp.read_text().splitlines()) > 100 and "## Contents" not in rp.read_text(): probs.append(f"{ref} >100 lines without '## Contents'")
        for m in TIME_RELATIVE.finditer(body): probs.append(f"time-relative phrasing: {m.group(0)!r}")
        status = "ok  " if not probs else "FAIL"
        print(f"{status} {skill_md.parent.name:32} lines={len(text.splitlines()):4} desc={len(desc or ''):4}")
        for pr in probs: print(f"       - {pr}")
        failures += bool(probs)
    dangling = sorted({r for r in re.findall(r"\b[a-z]+-livekit-[a-z]+\b", all_text + (ROOT/"README.md").read_text() + (ROOT/"AGENTS.md").read_text()) if r not in names})
    if dangling: print(f"FAIL dangling skill references: {dangling}"); failures += 1
    print("\nALL GOOD" if not failures else f"\n{failures} problem group(s)")
    return 1 if failures else 0

if __name__ == "__main__":
    sys.exit(main())
