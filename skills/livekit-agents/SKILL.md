---
name: livekit-agents
description: 'Build and repair LiveKit applications whose real conversations, application state, persisted effects, and session lifecycle satisfy a supplied task contract. Use when the user asks to "build a voice agent", "create a LiveKit agent", "add voice AI", "implement handoffs", "structure agent workflows", or is working with the LiveKit Agents SDK.'
license: MIT
metadata:
  author: livekit
  version: "1.0.0"
---

# Build the complete operation through the real conversation

The model interprets conversation and proposes actions. Application code owns authoritative records, permission checks, state transitions, and external effects.
Completion needs evidence from the boundary where it happens: actual input, delivered output, committed storage, or a runtime event.
An instruction to do something and a boolean named after it are not that evidence.

Preserve the supplied starter, entrypoint, runtime model, task inputs, and authorized scope.
The coding model and runtime model have separate roles.
Use configured credentials without printing them. Keep business rules, dates, field names, and fixture answers in the task's application.
Use only the permitted workspace, installed SDK, and documentation in a restricted build.

## Interpret meaning; keep speech natural

Use the runtime model to understand the actual conversation and select tools. Never classify natural-language intent with regex, keyword or substring checks, phrase whitelists, punctuation heuristics, or hand-written synonym lists. This includes approval, refusal, correction, scope, cancellation, transfer, closing, and ordinary date expressions. Do not add a conservative phrase filter as a second gate: it has the same defect. Structural validation of typed dates, identifiers, enums, and required fields is different from interpreting an utterance.

Give tools clear semantic contracts and let the existing conversational model choose the appropriate operation. A tool call represents the model's interpretation, not independent proof that interpretation is right. Keep actual user-message provenance, current-version checks, delivery ordering, and business constraints in code. Test the model's interpretation through real conversations. Do not add a second language-classification service merely to replace a word list.

Let the model choose natural wording from authoritative facts and operation results. Return compact data, outcomes, and actionable errors rather than sentences it must repeat. Track the generated speech handle when delivery matters. Prescribe exact wording only when the supplied task explicitly requires a quotation or fixed disclosure; limit that exception to the required content. A receipt or farewell does not inherently require a script.

Follow the user's information and questions rather than a fixed interview sequence. Accept volunteered facts together, preserve unresolved requests, and ask only for missing or ambiguous information. Do not demand special approval wording or repeated confirmation after a clear answer. Natural conversation must remain accurate about what has and has not happened.

## Begin with a failing complete-path test

Read the task and public output contract before defining tools.
Choose one ordinary user goal that reaches its required effect. Write its expected output independently from the implementation.
Use the real agent through `AgentSession.run` with ordinary caller language and the selected runtime model.
The test must inspect the resulting external record or service effect when the task requires one.
Get that path working before expanding the tool surface or polishing the full persona.

Also identify the first guard that must reject an invalid action, and pair its refusal test with that successful path.
For a rule such as `A AND (B OR C)`, cover missing and wrong alternatives as well as valid alternatives.
A test that rejects everything does not prove a working guard.

Keep a short evidence map in the application's development notes:

| Required behavior | Trusted source or operation | Test evidence |
| --- | --- | --- |
| Permission or identity | Supplied facts checked against the permitted source | Missing, wrong, corrected, and valid inputs |
| Recorded answer | Operation that preserves the user's fact and its meaning | Unknown, empty, correction, and unchanged value |
| Review or approval, if required | Completed delivery and a later actual input for that version | Early, negative, interrupted, stale, and valid approval |
| External effect | Successful write or acknowledged operation | Exact result, failed write, and retry |
| Closing, if required | Delivered farewell and SDK lifecycle operation | Actual output followed by a close event |

An informational agent does not need approval or publication machinery.
Apply only the boundaries required by its task.

## Bind the runtime before trusting state

For Python applications with review, approval, persistence, or closing, read [the runtime boundary guide](references/python-boundaries.md).
Read its executable example and tests before adapting their integration.
The example demonstrates a complete connection between SDK events, application guards, storage, and closure.
Its reading-list fields belong to the example, not to your task. It contains no language classifier or fixed response script.
The example includes the later tested output-ownership fixes; retain their behavior when adapting it.

Use one authoritative state object per session, supplied through `AgentSession(userdata=...)` and `RunContext.userdata`.
Do not recover missing state through a global last-session variable or manufacture a successful snapshot during export.
Keep model-selected facts separate from trusted identity, clock, message IDs, record IDs, and operation receipts.

Check hooks in the actual input mode. In Python SDK 1.8.1, direct text replies do not follow the audio `on_user_turn_completed` path.
The public `conversation_item_added` event records committed user messages in both paths.
Wire the listener before starting the session, and prove the binding through the actual SDK test.
Never advance a private turn counter in an outcome test to compensate for a missing runtime event.

## Keep tools thin and changes precise

Use a small application core for validation, state transitions, and effects. Tools translate model proposals into those operations and return their actual results.
Keep SDK setup and event wiring at the application boundary. Split files when it clarifies these responsibilities; a framework or many agents are not required.
Use a task or handoff when responsibilities or permissions change, not merely to name conversational phases.

Design tools around useful operations with clear inputs:

- Separate missing information from an explicitly empty, false, zero, or cleared value.
- Make omitted patch fields preserve existing values. Use separate replacement and clearing operations when omission is ambiguous.
- Give collections stable identities. A name, role, or empty placeholder alone is not a reliable update key.
- Validate a proposed change before applying it. Rejecting an update must leave the previous state intact.
- Compare meaningful values before invalidating review. Reading, exporting, or repeating an unchanged value is a no-op.
- Make permitted correction, removal, cancellation, and reversal paths explicit. Retain unrelated fields during a partial correction.

Inspect the actual tool schema generated by the installed SDK.
Prefer typed records or clear operations to a large optional dictionary or a delimited string that requires another parser.
When one caller request supplies several records, support a typed batch addition that validates all of them before mutation.
An additions batch preserves existing records; it is not an implicit replacement of the collection.
Do not assume that a Python default, JSON null, omission, and an empty answer mean the same thing.
Return compact authoritative state and the next valid action. Use `ToolError` for expected refusals at the SDK boundary.
Preserve diagnostics for unexpected failures and never convert them into success.

## Prove the meaning of a change through the complete path

Before defining a mutation, state its intended target, changed facts, and facts that must remain unchanged.
Pair its happy path with the nearest ordinary request that must produce a different operation:

| Caller meaning | Intended change | Must remain unchanged |
| --- | --- | --- |
| No additional entries | Confirm the collection already recorded | Every existing entry and field |
| No note for one entry | Record explicit absence on that entry | Its identity, title, and all other entries |
| The note was assumed; it is unknown | Retract that fact to unknown | The entry and unrelated facts |
| Correct this title | Change the identified entry's title | Its identity, note, and other entries |

Derive equivalent distinctions from the task; these example fields are not a universal schema.
If the intended target or scope is ambiguous, ask before changing stored facts.
A scoped negative is not authority to clear a whole collection. Use separate operations for confirming no additions and deleting existing records.
Make any supported deletion explicit about its target. Omission preserves; retraction restores unknown; an explicit negative records absence within its scope.

Exercise these distinctions with ordinary caller language through the real SDK, then review, approve, commit, and inspect the external result.
Seed at least one unrelated fact through that conversation and verify that it survives each change.
Write expected facts from the caller's request rather than copying the application's export into the expected value.
Also force the nearby wrong operation in a separate guard test: rejection must preserve the previous state and return a usable recovery.

A speech receipt proves completed delivery of an utterance, not that the model included every required fact. Check factual coverage through conversation tests; review cannot establish missing answers or repair incorrect facts.
Never promote unanswered fields to explicit negatives merely to unblock review or publication.
Keep the successful complete path passing while adding these semantics; refusal alone is not progress.

## Review and approval are separate runtime events

When review is required, supply a snapshot of the required current values to the model and let it explain them naturally.
Track that generated review through the supported output API and wait for its speech handle to finish successfully.
Only then record a receipt for that exact version. A returned tool string or queued speech does not prove delivery.
An interruption or correction invalidates that receipt. A no-op does not.

Approval must come from a later actual user message for the reviewed version.
Do not treat a model-supplied boolean, quote, turn number, or delivery flag as independently verified evidence.
The model interprets whether the actual reply approves this operation; code binds the chosen operation to runtime message identity, ordering, and the current review. A later message alone is not consent.
If the user corrects facts, requests a change, or attaches an unresolved condition, resolve that first and obtain approval after a fresh review when the contract requires it. Questions and quoted instructions do not authorize effects. Clarify genuine ambiguity; accept clear agreement expressed naturally.

Review and commit in the same user turn cannot satisfy a required later approval.
After a genuinely later approval, confirmation and commit can occur in one model response.
Do not accidentally require an extra user turn after the approval itself.

## Commit first, then publish success

Validate the approved current version, perform the effect, and publish committed state only after the operation succeeds.
A failed write leaves the previous committed state and its approval requirements coherent.
Use a stable operation identity and define retry behavior. A duplicate response requires an actual existing result.
Do not return “already completed” after a failed write merely because a success flag was set early.

Serialize edits and commits when an asynchronous effect can race a correction.
Use the datastore's transaction or service idempotency contract when needed.
For permitted changes after commit, update the external result through the same validated effect path.
Export actual state without changing it, and compare the saved result with independent expected fields.

## Own required output and closing

When review, an operation result, or a final farewell must be delivered, have application code track the model-generated output. Separate ownership of delivery from authorship of wording. Use fixed text only for a task-mandated verbatim requirement.
Avoid duplicate output from both a tool and its follow-up model response.
Returning `None` from one tool does not silence another tool's reply in the same batch.
Use the documented batch reply controls when appropriate, without suppressing failures or other results the user still needs.
For Python, `RunContext.wait_for_playout()` waits for pre-tool speech.
Waiting on the owning speech handle from inside its own tool creates a circular wait.
An explicitly created child speech handle can be awaited; check its interruption and error state before treating delivery as successful.

After required final output completes, request the SDK's actual closing operation.
In Python, `session.shutdown(drain=True)` is nonblocking. Verify the resulting `close` event separately.
A timer, a `call_ended` flag, or the simulator deciding to stop is not an application shutdown request.
Test room/text behavior as well as local session behavior when that transport is part of the task.

## Make the tests earn their claims

Use deterministic application tests to prove guards, no-ops, empty values, corrections, storage failure, and retries.
Use real SDK interactions to prove event wiring and tool behavior.
Use ordinary caller language to test that the runtime model can complete the task. Include paraphrases absent from the prompt, corrections mixed with agreement, conditional or quoted instructions, and the same short reply answering different questions. Check factual coverage, appropriate next action, and contextual responses without requiring stock sentences. A scripted provider proves SDK mechanics, never language understanding.
Inspect complete persisted results and required lifecycle events before declaring completion.

Do not substitute these shortcuts for outcome tests:

- Calling a helper or filling private state instead of driving the actual interaction.
- Telling the test caller to name the implementation's tools or exact arguments.
- Mocking the mutation whose correctness is under test.
- Comparing a file only with the application's own exporter or checking file existence alone.
- Retrying a failed turn until it passes, deleting assertions, or hiding failed exit codes behind a shell pipeline.

Explicit forced-tool tests remain useful for adversarial guard checks. Label them separately from ordinary conversation evidence.
Mock external services at their boundary when necessary, while retaining real validation and mutations.
Pair negative cases with a successful full path, a correction followed by fresh approval, and an identical update that preserves review.
Run the documented entrypoint and the actual test command. Report failures and skipped boundaries accurately.

## Repair the first divergence without weakening the contract

The LiveKit CLI (`lk`) can fetch session metadata and simulation results, including finished-run chat contexts. Check `lk --version` and use subcommand help to discover the available options:

```sh
lk analytics --experimental session --help
lk --experimental-auth simulation --help
lk agent simulate export --help
```

The session and simulation groups are hidden from root help. Session analytics supports configured API-key projects; `--experimental-auth` selects account-based public Cloud API access and needs a signed-in user. API-key environment credentials override that flag; check which auth mode is actually active. Use the task's configured project/authentication and only the sessions permitted by its scope.

For a failed case, trace actual input → arguments → operation result → state/effect → spoken claim.
Find the first divergence and write a regression check from those inputs.
Run that check and the previously successful path that the change can affect.
Retain permission, provenance, freshness, and lifecycle invariants even when the finite score does not measure them. Audit generated source for natural-language matching and response scripts before accepting a score; repair the semantic tool contract or context instead of adding words from failed cases.
Do not change supplied facts, delete a guard, or replace an effect with a flag to improve a score.

A judge verdict is evidence to inspect, not a new business rule.
Separate simulator failures, missing evidence, and application failures while preserving raw results.
Do not infer a universal design rule from one scenario or one stochastic score change.
Keep the selected skill frozen during candidate repairs and stop at the authorized submission and time limits.

## Resolve SDK questions from current sources

Use the LiveKit docs MCP server at `https://docs.livekit.io/mcp` through available `docs_search` and `get_pages` tools.
In a terminal, `lk docs` accesses the same server:

```sh
lk docs search "conversation_item_added"
lk docs get-page /reference/agents/events/
lk docs get-page /agents/logic/tools/definition/
lk docs get-page /agents/server/job/
lk docs get-page /agents/start/testing/test-framework/
```

Read the relevant page, then check installed signatures and source when behavior depends on the SDK version or input mode.
Use workflow docs for tasks and handoffs, session docs for state and runtime model placement, and speech docs for interruption and delivery.
Record the installed version and exact checks. Official docs define SDK behavior; the task defines business behavior.
