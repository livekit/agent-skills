---
name: reading-livekit-docs
description: 'Looks up current, verified facts about LiveKit — API signatures, CLI flags, config options, model and provider support, SDK changelogs, pricing — instead of answering from memory. Use whenever a question touches LiveKit specifics: "does LiveKit support X", "what changed in agents 1.8", "what are the arguments to Y", "how much does LiveKit cost", "find an example of Z in the LiveKit repos", or before writing any LiveKit code. Other LiveKit skills load this one first. Covers the LiveKit Docs MCP server and the `lk docs` CLI.'
license: MIT
metadata:
  author: livekit
  version: "1.0.0"
---

# Reading LiveKit documentation

LiveKit's SDKs move faster than model training data. Anything you "remember" about a LiveKit API,
CLI flag, or default is a guess, and guesses here are expensive: a wrong flag wastes a run, a wrong
signature wastes a build.

**The rule: every LiveKit-specific fact you state or write into code comes from a lookup in this
session.** Not from memory, not from a pattern that looked right in another repo. This applies even
when you are confident — especially then.

## Three ways in, in order of preference

**1. The LiveKit Docs MCP server.** If its tools are present in your session, use them. They're the
same source the CLI uses, with the least friction.

**2. `lk docs`.** Available wherever the LiveKit CLI is installed, with no MCP setup. Use it when
MCP tools are absent — don't stop to ask the user to install anything first. It can search the docs,
fetch pages, search LiveKit's own code across its repositories, show an SDK's recent changelog, report
pricing, and submit feedback. Start with:

```bash
lk docs --help
lk docs search "agent simulations"
```

and fetch the page you want once search has shown you which one it is. Machine-readable output is
available when you'd rather parse than read.

**3. Web search against `docs.livekit.io`.** Last resort, when neither of the above is available.
Say so explicitly, and mark generated code as unverified.

## How to research, not just search

- **Search before you read.** Search returns per-page excerpts, which is usually enough to pick the
  right page. Fetch a full page only once you know which one you want — pulling whole pages you
  don't need is what fills a context window with nothing.
- **Use code search for *how*, docs for *what*.** Docs tell you a parameter exists; LiveKit's own
  examples show how it's actually called. When a docs page and a real example disagree, prefer the
  example and say you saw a discrepancy.
- **Use the changelog for anything version-shaped.** "Is X available yet", "when did Y change", "why
  does this argument not exist" are changelog questions, not search questions.
- **Check the version you're actually on.** The installed SDK and CLI decide what works, not the
  newest docs. A documented feature is not a present feature. For any CLI command, `--help` on the
  installed binary outranks every other source.

## Reporting what you found

- **Cite the page.** When a decision rests on a doc, name it. It's how the user checks you.
- **Say when you couldn't verify.** "I could not confirm this signature against the docs" is a
  useful sentence. Silently guessing is not.
- **Mark unverified code.** If you had to write LiveKit code without a lookup, comment it as
  unverified at the call site and say so in your reply.
- **Never invent a flag or parameter to make an example look complete.** An incomplete example
  with a note beats a plausible fabrication.

## When the docs are wrong

You will sometimes find a page that contradicts the SDK source or the CLI's own `--help`. Two
useful reflexes:

- **Trust the thing that runs.** `--help`, the installed SDK's source, and a working example outrank
  a prose page. Tell the user which you followed and why.
- **Report it** through the docs feedback command, and mention to the user that you did. A docs bug
  you hit is a docs bug the next person hits.

A version-skew warning from `lk docs` (the docs server being a little ahead of the CLI calling it)
is routine and doesn't invalidate results. Suggest `lk` be updated; keep using the results.

## Related skills

- Building an agent: `building-livekit-agents`
- Live-testing one during development: `debugging-livekit-agents`
- Unit tests: `testing-livekit-agents`
- Simulations: `writing-livekit-scenarios`, `running-livekit-simulations`
