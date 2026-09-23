# Writing instructions a simulated user follows well

## Contents
- Two shapes: point-form direction, and persona-and-goals
- Rules that hold for both shapes
- Varying the cast across a suite
- Identity details in instructions
- Scenarios written for audio

The simulated user is an LLM reading `instructions` and improvising a conversation. How you write
them decides whether a run is repeatable or a different conversation every time — and the right
answer differs by what the scenario is for.

## Two shapes

### Point-form direction — for deterministic flows

When a scenario drives a concrete flow to a known end state and you grade on that state, you need
the simulated user on rails. A structured, labelled template steers far more reliably than prose:

```
PERSONA: who they are, and any speech detail that matters (spelling a name only if asked)
OPENING LINE: the exact first thing they say
FACTS (reveal each only when asked, one per turn):
  - the details the agent must collect
DO, IN ORDER:
  - the steps they take, in sequence
REACTIONS:
  - conditional behavior: if the agent offers X, decline; if it asks twice, get impatient
HIDDEN TRUTH: what's actually true, which the agent must discover
```

Two things make this work. **Facts revealed one per turn when asked** forces the agent to actually
run its collection flow instead of receiving everything in the opening line. **Steps in order** keeps
the path stable across runs, which is what makes final-state grading meaningful.

Where a scenario grades on final state, repeat the pinned values (dates, contact details, options)
verbatim in both the instructions and the expected state, so the comparison can match.

### Persona and goals — for open-ended and adversarial scenarios

When you're grading the conversation itself and want the simulated user to improvise, over-direction
defeats the point. Use a short persona — communication style and mood, third person — then a handful
of atomic goals:

```
A brisk regular who has done this before and doesn't want small talk.

Goals:
- Ask what's available tomorrow afternoon
- Change their mind about the time once the agent offers something
- Finish with a confirmed booking
```

## Rules that hold for both shapes

- **The simulated user talks *to* the agent.** Goals are requests ("order a large fries"), never the
  agent's own actions ("greet the caller", "process the order"). A simulated user performing the
  agent's job is the most common broken scenario.
- **Only what the agent handles.** Ground every goal in real capabilities. Don't ask a drive-thru for
  delivery unless testing exactly that refusal — and then say so in the expectation.
- **Real domain values.** Actual item names, sizes, times from the agent's domain.
- **No prior state.** Each goal reads independently. "Order a Big Mac" then "remove the Big Mac",
  never "remove the Big Mac that was already added".
- **Mix difficulty.** Mostly straightforward, some with a mid-conversation change of mind, a few
  genuinely hard.

## Vary the cast

Choose a distinct persona, mood, and situation per scenario, and spread them widely — age, tone,
tech-savviness, urgency, patience, how cooperative they are. Keep their circumstances consistent with
how they'd plausibly reach this agent.

Spread the suite across framings so it isn't monotone:

- **Routine** — the everyday request, handled constantly.
- **Common but characterful** — a normal request made interesting by who's making it.
- **Uncommon but plausible** — realistic, not typical.
- **Stress** — difficult-but-realistic behavior for this domain.

For stress cases, give the caller a **communication challenge** — hostile, evasive, refuses to
verify, tries to befriend the agent, talks around the question. The difficulty should be in *how*
they talk, while the underlying request stays realistic. A caller with an absurd request tests
nothing; a reasonable caller who won't answer questions tests a lot.

Also spread across the agent's actual range. Don't test only the first or most popular item.

## Identity details

Put the identity the scenario needs directly in the instructions — name, contact details, payment
details where the flow requires them — using clearly fictional values. Keep them consistent with any
seeded state and with the expected end state.

It is fine, and often the point, for a caller to *lack* a credential: no order number, no PIN, can't
verify. Don't invent a specific wrong value unless the scenario is specifically about a mismatch.

## Scenarios written for audio

Most scenarios should run in text. Write a scenario *for* audio when the thing under test only
exists in speech:

- **Entities that survive transcription** — spelled-out names, confirmation codes, account numbers,
  amounts, addresses. Put them in the instructions deliberately and require them back correctly.
- **Turn-taking and interruption** — a caller who interrupts mid-sentence, trails off, pauses to
  think, or answers before the agent finishes.
- **Recovery from bad input** — a caller on a poor connection or in a noisy place, where the agent
  should ask for a repeat rather than guess.

These scenarios are worth writing in a set of their own: audio runs are slow and expensive, so you
want to run them deliberately rather than dragging the whole file through the audio pipeline.
