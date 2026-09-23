---
name: running-livekit-simulations
description: 'Runs LiveKit agent simulations and acts on the results. Use when the user says "run my simulations", "run the scenarios", "use lk agent simulate", "did my agent pass", "why did this scenario fail", "run simulations in CI", "test the audio pipeline", "check turn-taking and interruptions", or wants to verify whole-conversation behavior before shipping. Covers text versus audio mode and what each catches, running against a local or deployed agent, degraded-audio flags, automating a pre-release run, and triaging failures with list, view and export. For authoring the scenarios use writing-livekit-scenarios. Not the default for a bare "test my agent" — that is debugging-livekit-agents; use this skill when the user names simulations, scenarios, a run, CI, or shipping.'
license: MIT
metadata:
  author: livekit
  version: "1.0.0"
---

# Running LiveKit simulations

A simulation plays a scenario against the real agent with an LLM-driven simulated user, then a judge
grades the transcript. Unlike a unit test, which asserts on one turn, a simulation answers whether a
*whole conversation* reached the right outcome.

Read `lk agent simulate --help` before running — subcommands and flags change, a wrong flag wastes
a real run, and this skill deliberately doesn't restate them. `reading-livekit-docs` has the rest.

## When to reach for a simulation

Simulations are the most thorough check available and the most expensive: every scenario spends
tokens on the simulated user, on the agent, and on the judge. That cost decides where they belong.

| Question | Use |
|---|---|
| Does this behave the way I meant, right now? | `debugging-livekit-agents` |
| Is this exact turn still correct? | `testing-livekit-agents`, on every commit |
| Does the whole conversation reach the right outcome? | Simulations, before you ship |

Run them before a release, on a release branch, or when a change touches conversation flow — not on
every commit. Things only simulations catch: multi-turn flow when the caller backtracks, details
gathered early surviving to the end, whether the agent holds its instructions under pressure, and
whether the conversation ended in the right *state*.

## Running

Run from the agent's project directory. The mode is a subcommand:

```bash
lk agent simulate text --scenarios scenarios.yaml    # see --help for the current flags
```

With no scenario file, the CLI generates scenarios from the agent's source, which **uploads the
code** and prompts for confirmation first — see `writing-livekit-scenarios`, which is where generation
belongs.

By default the CLI starts the agent as a local worker, dispatches the scenarios to it, and stops it
when the run ends. There's an option to grade an already-running agent by name instead; that needs
a scenario file, since there's no local source to generate from.

Concurrency is bounded per run and per project; the docs have the current limits.

## Text or audio

**Text is the default and the right default.** The simulated user exchanges text with the agent, so
the run exercises the LLM, the tools, and the conversation logic while the framework disables STT,
TTS and VAD. Faster, cheaper, more deterministic. Use it for iteration and for anything automated.

**Audio runs the same scenarios through the full speech pipeline.** The simulated user speaks,
listens, and interrupts like a real caller, and the run scores what only speech exposes:

- **Turn-taking** — starting to speak before the caller finished, or leaving a finished caller waiting.
- **Interruption handling** — yielding to a barge-in, and telling a brief acknowledgment from a turn.
- **Transcription accuracy** in both directions, scored separately for the things that matter:
  names, numbers, addresses, confirmation codes.
- **Perceived latency** — what the caller actually heard, which is not what the agent reports about
  itself. The gap between the two is the user's experience.

Audio runs execute in real time, call the STT and TTS providers every turn, and meter at a higher
rate. Reserve them for a release candidate or a change that touches speech, turn-taking, or
interruption — not for a recurring job.

The audio subcommand has options to degrade the simulated caller's audio — noise, a poor
microphone, packet loss. Use them to test what the agent does with speech it can't cleanly hear:
the desired behavior is asking for a repeat, not guessing. Combine them for a worst-case caller.

## Automating a pre-release run

A committed scenario file plus a scheduled or release-branch job is the whole setup. The CLI is
built for this — plain output when it isn't attached to a terminal, a failing exit code when any
scenario fails — so the job fails on its own. The docs have a worked CI example to start from.

What actually goes wrong in automation:

- **The CLI starts the real agent**, so the job must install the agent's dependencies and provide
  every API key the agent itself reads — not just LiveKit credentials.
- **Keep credentials in secrets.** A key inlined in a committed workflow is a leaked key.
- **Keep automated runs in text mode.** Text simulations are scheduled so they don't compete with
  live sessions for inference capacity; audio runs don't have that property, and cost far more.
- **Pin scenarios to absolute dates**, or the suite starts failing months later for no reason.
- **Every scenario in the committed file must pass.** A scenario the agent has never passed blocks
  every release. Fix the agent, sharpen the expectation, or keep the aspirational ones in a separate
  file run on demand.

## Reading the results

A run prints a per-scenario verdict and a dashboard link. Work from the transcript, not the verdict
line — the verdict says what happened, the transcript says why.

The CLI has subcommands to list recent runs, reopen one, and export a finished run with its
per-scenario chat contexts as JSON (`--help` names them). Export is the one to reach for when
comparing behavior between runs or archiving a run as a build artifact.

**Triage a failure by deciding which of three things it is:**

1. **A real bug.** Fix the agent and re-run. Suspect instructions and tool descriptions first — a
   failure that looks like faulty reasoning is often a tool whose description never says when to use
   it.
2. **A bad scenario.** The expectation requires something the agent shouldn't do, or is too vague for
   a judge to decide consistently. Fix the scenario; a vague `agent_expectations` is the most common
   cause of a verdict that flips between runs.
3. **A missing piece of the simulated world.** The scenario passes but production failed, or vice
   versa — usually because the agent reached different data, the derived instructions omit the turn
   that caused the problem, or the failure was audio-only and a text run can't see it.

**After a fix, run the whole file**, not just the scenario you were working on. A fix aimed at one
conversation routinely changes a neighbouring one.

**Move repeat failures down the stack.** A scenario that fails the same way every time is describing
a turn-level bug; a unit test pins it more cheaply and catches it earlier. See `testing-livekit-agents`.

## Related skills

- Authoring and organizing scenarios: `writing-livekit-scenarios`
- Interactive debugging of a failure: `debugging-livekit-agents`
- Cheaper per-commit coverage: `testing-livekit-agents`
- Flags, versions, changelogs: `reading-livekit-docs`
