# One complete operation with precise edits

Read [the application](../assets/python/editable_records.py), its
[core tests](../assets/python/test_editable_records.py), and its
[scope tests](../assets/python/test_scoped_records.py). The
[SDK tests](../assets/python/test_editable_records_sdk.py) exercise real event
wiring with a scripted provider. The [ordinary-language tests](../assets/python/test_scoped_conversation.py)
exercise the same agent with the selected runtime model. The
[context tests](../assets/python/test_contextual_conversation.py) distinguish
agreement, correction, questions, and quoted instructions. The
[natural-output SDK tests](../assets/python/test_natural_boundaries.py) verify
that delivery tracking accepts generated wording.

The example prepares and publishes a reading list. It joins application-issued
entry IDs, partial edits, review delivery, later actual approval, atomic storage,
spoken results, and SDK closing. It is a teaching application; adapt its fields
and permitted operations to the user's task.

`RecordBook` owns the entries. `RecordsAgent` translates model proposals into its
operations. Each result returns the current records and a valid next action.
The mutation methods validate proposed fields before assigning them. Unchanged
values preserve the review. A real change invalidates it.

`add_entries` accepts all new entries supplied together in one typed batch.
It validates the entire batch before changing state and retains existing entries.
This avoids requiring a separate model decision for each entry in a single request.
Corrections use the returned IDs; they never add replacements.

`confirm_entries` means no additional entries. It preserves all existing facts.
`confirm_empty` accepts an explicitly empty initial list and refuses to erase
existing entries. `remove_entry` deletes one identified entry. An application
that supports whole-list deletion needs a separate, explicit contract for it.
Do not turn a negative answer about one person, object, or field into deletion
of an entire collection.

An omitted correction field preserves its value. `clear_note` records explicit
absence on one entry. `mark_note_unknown` retracts that entry's note to unknown.
The model explains the stored state in its own words. Neither review nor approval fills in
missing facts. A reading-list note is optional; unknown does not block this
example's publication. Each real task defines its own required facts.

Bind actual caller messages before starting the session. The example's
`create_agent_session` factory requires explicit STT and TTS components for voice.
It permits omitted voice components only with `text_test=True`. Preserve the
starter's VAD, room setup, and other voice configuration around this composition.

The output listener waits until sibling tools finish, then asks the model to generate a review
or farewell from the settled facts with further tools disabled. It preserves independent results and publication receipts until
owned output finishes. A receipt is created only for nonempty, completed output and the
same requesting user message. It stores the actual generated utterance; it does
not prove semantic completeness. Conversation tests check that separately. Closing reports publication success or failure
before requesting `session.shutdown(drain=True)`.

The separate `close` event proves local session closure. Room and telephony
teardown need their own transport checks. Text tests do not prove microphone,
TTS, or audio-interruption behavior.

Publication checks runtime user-message identity, sequence, delivery time, and
current version. The model chooses publication only when it interprets the actual
reply as approval of that reviewed list. There is no phrase grammar, regex, or
keyword fallback. Calling the core publication method in a unit test bypasses
interpretation; only real-model conversations test that responsibility.
The publication ID stays stable across a failed-write retry.

Use a storage path scoped to the actual session or principal. The small local
write is synchronous and uses atomic replacement. Slow asynchronous effects
need serialization and an explicit policy for uncertain outcomes.

SDK behavior was checked against the installed SDK and official documentation:

- [Tool arguments, results, speech, and errors](https://docs.livekit.io/agents/logic/tools/definition/).
- [SDK interaction tests](https://docs.livekit.io/agents/start/testing/test-framework/).
- [Job and session lifecycle](https://docs.livekit.io/agents/server/job/).

The example returns structured format and publication results. It has no fixed
review question or farewell. Its child `generate_reply` has `tool_choice="none"`;
its completed speech handle supplies the delivery receipt. This does not add a
separate classifier or a second model. The deterministic SDK tests use scripted
provider responses strictly as fixtures; their exact sentences are not application
requirements or evidence of natural-language understanding.

Keep three kinds of evidence distinct: deterministic domain guards, scripted
SDK execution, and ordinary-language model behavior. Passing these example
tests does not establish that a generated consumer preserves the same contract.

Run offline checks with `python -m pytest -q`. The model tests are skipped
unless `RUN_LIVE_SCOPED=1` is set with `MODEL` and configured LiveKit credentials:

```sh
RUN_LIVE_SCOPED=1 MODEL=provider/runtime-model python -m pytest test_scoped_conversation.py test_contextual_conversation.py -q
```

Preserve failed conversations. Change code only for an observed defect, then
record the new source version before evaluating it. Do not retry unchanged
conversations until they pass or substitute scripted tool calls for model behavior.
