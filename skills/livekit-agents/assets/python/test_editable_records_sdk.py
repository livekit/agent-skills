"""Deterministic SDK interactions with scripted tool proposals, not model interpretation."""

import asyncio
import json
from collections import Counter
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from editable_records import JsonStore, RecordsAgent, create_agent_session
from livekit.agents import RunContext, function_tool, llm
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS
from livekit.agents.voice import io


def call(name, **arguments):
    return llm.FunctionToolCall(
        name=name, arguments=json.dumps(arguments), call_id=uuid4().hex
    )


class ScriptedModel(llm.LLM):
    def __init__(self, responses):
        super().__init__()
        self.responses = responses
        self.calls = Counter()

    def chat(
        self,
        *,
        chat_ctx,
        tools=None,
        conn_options=DEFAULT_API_CONNECT_OPTIONS,
        **kwargs,
    ):
        user = next(
            item.text_content
            for item in reversed(chat_ctx.items)
            if isinstance(item, llm.ChatMessage) and item.role == "user"
        )
        index = self.calls[user]
        self.calls[user] += 1
        responses = self.responses[user]
        # A visible sentinel avoids retries or hangs obscuring an unwanted reply.
        response = (
            responses[index] if index < len(responses) else "UNEXPECTED MODEL FOLLOW-UP"
        )
        if callable(response):
            response = response(chat_ctx)
        return ScriptedStream(self, chat_ctx, tools or [], conn_options, response)


class ScriptedStream(llm.LLMStream):
    def __init__(self, model, chat_ctx, tools, conn_options, response):
        self.response = response
        super().__init__(
            model, chat_ctx=chat_ctx, tools=tools, conn_options=conn_options
        )

    async def _run(self):
        delta = (
            llm.ChoiceDelta(content=self.response)
            if isinstance(self.response, str)
            else llm.ChoiceDelta(tool_calls=self.response)
        )
        self._event_ch.send_nowait(llm.ChatChunk(id=uuid4().hex, delta=delta))


def assistant_messages(session):
    return [
        item.text_content
        for item in session.history.items
        if isinstance(item, llm.ChatMessage) and item.role == "assistant"
    ]


def user_message(session, text):
    return next(
        item
        for item in session.history.items
        if isinstance(item, llm.ChatMessage)
        and item.role == "user"
        and item.text_content == text
    )


async def run(session, text):
    return await asyncio.wait_for(session.run(user_input=text), timeout=5)


class GatedText(io.TextOutput):
    def __init__(self):
        super().__init__(label="deterministic text transport", next_in_chain=None)
        self.enabled = False
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def capture_text(self, text):
        if self.enabled:
            self.started.set()
            await self.release.wait()

    def flush(self):
        pass


@asynccontextmanager
async def opened(tmp_path, responses, *, agent_type=RecordsAgent, sink=None):
    async with ScriptedModel(responses) as model:
        store = JsonStore(tmp_path / "records.json")
        session, agent = create_agent_session(
            store=store, llm=model, stt=None, tts=None, text_test=True
        )
        if agent_type is not RecordsAgent:
            agent = agent_type(store)
        if sink:
            session.output.transcription = sink
        async with session:
            await session.start(agent)
            yield session, session.userdata, store, model


def initial():
    return {
        "Add Birds with illustrated notes.": [
            [call("add_entries", entries=[{"title": "Birds", "note": "Illustrated"}])],
            "Added Birds.",
        ]
    }


async def seed(session, state):
    await run(session, "Add Birds with illustrated notes.")
    return state.records()[0]["entry_id"]


@pytest.mark.asyncio
async def test_scope_correction_review_and_commit_share_the_real_sdk_path(tmp_path):
    responses = {
        "Add Birds and Trees.": [
            [
                call(
                    "add_entries", entries=[{"title": "Birds", "note": "Illustrated"}]
                ),
                call("add_entries", entries=[{"title": "Trees", "note": "Shade"}]),
                call("review_records"),
            ],
            "Birds has the Illustrated note; Trees has Shade. May I publish both?",
        ]
    }
    async with opened(tmp_path, responses) as (session, state, store, model):
        closed = asyncio.Event()
        session.on("close", lambda _event: closed.set())
        await run(session, "Add Birds and Trees.")
        first, second = state.records()
        # Deliberately propose the nearby wrong operation. It must not erase
        # prior facts, and the SDK must deliver its error before the new review.
        responses["There are no other entries."] = [
            [call("confirm_empty"), call("review_records")],
            "Nothing has been deleted. Birds is Illustrated and Trees is Shade. Shall I publish them?",
        ]
        await run(session, "There are no other entries.")
        assert state.records() == [first, second]
        assert "Nothing has been deleted" in assistant_messages(session)[-1]
        assert model.calls["There are no other entries."] == 2
        assert not store.path.exists()
        request = (
            "The Birds note is unknown. Rename Trees to Forest trees; keep its note."
        )
        responses[request] = [
            [
                call("mark_note_unknown", entry_id=first["entry_id"]),
                call(
                    "correct_entry", entry_id=second["entry_id"], title="Forest trees"
                ),
                call("confirm_entries"),
                call("review_records"),
            ],
            "Birds has an unknown note; Forest trees has Shade. Are these ready to publish?",
        ]
        await run(session, request)
        expected = [
            {"entry_id": first["entry_id"], "title": "Birds", "note": None},
            {"entry_id": second["entry_id"], "title": "Forest trees", "note": "Shade"},
        ]
        assert state.records() == expected
        assert state.review is not None and "unknown note" in state.review.text
        approval = "Yes, publish it and finish."
        responses[approval] = [
            [call("publish_records"), call("finish_session")],
            lambda _: (
                f"Published as {state.publication['publication_id']}. Enjoy your reading!"
            ),
        ]
        await run(session, approval)
        await asyncio.wait_for(closed.wait(), timeout=5)
        saved = json.loads(store.path.read_text())
        assert saved["entries"] == expected
        assert saved["approved_message_id"] == user_message(session, approval).id
        assert state.closed and state.shutdown_requested
        assert saved["publication_id"] in assistant_messages(session)[-1]


@pytest.mark.asyncio
async def test_failed_edit_and_review_report_error_then_yield(tmp_path):
    responses = initial()
    request = "Try the invalid change, then review the actual entries."
    async with opened(tmp_path, responses) as (session, state, store, model):
        key = await seed(session, state)
        responses[request] = [
            [
                call("correct_entry", entry_id=key, title=" ", note="Large print"),
                call("review_records"),
            ],
            "The title cannot be blank, so Birds remains Illustrated. Shall I publish it?",
        ]
        await run(session, request)
        assert state.records() == [
            {"entry_id": key, "title": "Birds", "note": "Illustrated"}
        ]
        text = assistant_messages(session)[-1]
        assert "cannot be blank" in text and "Illustrated" in text
        assert text.endswith("Shall I publish it?")
        assert "Yes, I approve." not in assistant_messages(session)
        assert model.calls[request] == 2 and state.review is not None
        assert not store.path.exists()


@pytest.mark.asyncio
async def test_lookup_answer_survives_review_batch(tmp_path):
    responses = initial()
    responses["What format is supported? Review the list too."] = [
        [call("describe_format"), call("review_records")],
        "Each title has an optional plain-text note. Birds has Illustrated. Do you approve publishing it?",
    ]
    async with opened(tmp_path, responses) as (session, state, _store, _model):
        await seed(session, state)
        await run(session, "What format is supported? Review the list too.")
        text = assistant_messages(session)[-1]
        assert "optional plain-text note" in text
        assert text.index("optional plain-text note") < text.index("Do you approve")
        assert state.review is not None and state.publication is None


@pytest.mark.asyncio
async def test_lookup_answer_survives_a_later_review_batch_in_same_user_turn(tmp_path):
    responses = initial()
    request = "Explain the format, then review."
    responses[request] = [
        [call("describe_format")],
        [call("review_records")],
        "Each title has an optional plain-text note. Birds has Illustrated. Do you approve publishing it?",
    ]
    async with opened(tmp_path, responses) as (session, state, _store, _model):
        await seed(session, state)
        await run(session, request)
        text = assistant_messages(session)[-1]
        assert "optional plain-text note" in text
        assert text.index("optional plain-text note") < text.index("Do you approve")
        assert state.review is not None and state.public_results == {}


@pytest.mark.asyncio
async def test_edit_and_review_then_later_actual_approval_save_exact_record(tmp_path):
    responses = initial()
    responses["Review it."] = [
        [call("review_records")],
        "Birds has your Illustrated note. Ready to publish?",
    ]
    async with opened(tmp_path, responses) as (session, state, store, _model):
        key = await seed(session, state)
        await run(session, "Review it.")
        old = state.review
        correction = "Change the title to Trees, keep my note, and review it. Do not publish yet."
        responses[correction] = [
            [
                call("correct_entry", entry_id=key, title="Trees"),
                call("publish_records"),
                call("review_records"),
            ],
            "Publication needs your new approval. Trees retains Illustrated. May I publish it?",
        ]
        await run(session, correction)
        assert state.review.version > old.version and not store.path.exists()
        responses["Yes, publish it."] = [[call("publish_records")], "Published."]
        await run(session, "Yes, publish it.")
        saved = json.loads(store.path.read_text())
        assert saved["entries"] == [
            {"entry_id": key, "title": "Trees", "note": "Illustrated"}
        ]
        assert (
            saved["approved_message_id"] == user_message(session, "Yes, publish it.").id
        )


@pytest.mark.asyncio
async def test_publish_and_finish_deliver_receipt_before_close(tmp_path):
    responses = initial()
    responses["Review it."] = [
        [call("review_records")],
        "Birds has your Illustrated note. Ready to publish?",
    ]
    request = "Yes, publish it and finish."
    responses[request] = [
        [call("publish_records"), call("finish_session")],
        lambda _: (
            f"Published 1 entry with reference {state.publication['publication_id']}. Take care!"
        ),
    ]
    async with opened(tmp_path, responses) as (session, state, store, model):
        closed = asyncio.Event()
        session.on("close", lambda _: closed.set())
        await seed(session, state)
        await run(session, "Review it.")
        await run(session, request)
        await asyncio.wait_for(closed.wait(), 5)
        saved = json.loads(store.path.read_text())
        text = assistant_messages(session)[-1]
        assert saved["publication_id"] in text and "Published 1 entry" in text
        assert text.index(saved["publication_id"]) < text.index("Take care")
        assert model.calls[request] == 2 and state.closed and state.shutdown_requested


@pytest.mark.asyncio
async def test_failed_publication_then_finish_is_honest(tmp_path, monkeypatch):
    responses = initial()
    responses["Review it."] = [
        [call("review_records")],
        "Birds has your Illustrated note. Ready to publish?",
    ]
    request = "Yes, publish it and finish."
    responses[request] = [
        [call("publish_records"), call("finish_session")],
        "Publication failed; the list has not been published. Take care.",
    ]
    async with opened(tmp_path, responses) as (session, state, store, _model):
        await seed(session, state)
        await run(session, "Review it.")

        def fail(*args):
            raise OSError("deliberate replacement failure")

        monkeypatch.setattr("editable_records.os.replace", fail)
        closed = asyncio.Event()
        session.on("close", lambda _: closed.set())
        await run(session, request)
        await asyncio.wait_for(closed.wait(), 5)
        text = assistant_messages(session)[-1]
        assert (
            "Publication failed" in text
            and "has not been published" in text
            and text.endswith("Take care.")
        )
        assert not store.path.exists() and state.publication is None


class OtherAgent(RecordsAgent):
    @function_tool
    async def another_result(self, context: RunContext) -> dict:
        """Return a result whose speech renderer is not supplied by the example."""
        return {"reference": "outside-42"}


@pytest.mark.asyncio
async def test_unowned_result_keeps_reply_and_postpones_review(tmp_path):
    responses = initial()
    request = "Check the other reference and review."
    responses[request] = [
        [call("another_result"), call("review_records")],
        "The reference is outside-42. I can review next.",
    ]
    async with opened(tmp_path, responses, agent_type=OtherAgent) as (
        session,
        state,
        _store,
        model,
    ):
        await seed(session, state)
        await run(session, request)
        assert state.review is None and "outside-42" in assistant_messages(session)[-1]
        assert model.calls[request] == 2


@pytest.mark.asyncio
async def test_delivery_receipt_waits_for_actual_output(tmp_path):
    responses = initial()
    responses["Review it."] = [
        [call("review_records")],
        "Birds has your Illustrated note. Ready to publish?",
    ]
    sink = GatedText()
    async with opened(tmp_path, responses, sink=sink) as (
        session,
        state,
        _store,
        _model,
    ):
        await seed(session, state)
        sink.enabled = True
        pending = asyncio.ensure_future(session.run(user_input="Review it."))
        try:
            await asyncio.wait_for(sink.started.wait(), 3)
            assert state.review is None and not pending.done()
        finally:
            sink.release.set()
            await asyncio.wait_for(pending, 3)
        assert state.review is not None


@pytest.mark.asyncio
async def test_interrupted_review_cannot_authorize_publication(tmp_path):
    responses = initial()
    responses["Review it."] = [
        [call("review_records")],
        "Birds has your Illustrated note. Ready to publish?",
    ]
    sink = GatedText()
    async with opened(tmp_path, responses, sink=sink) as (
        session,
        state,
        store,
        _model,
    ):
        await seed(session, state)
        sink.enabled = True
        pending = asyncio.ensure_future(session.run(user_input="Review it."))
        await asyncio.wait_for(sink.started.wait(), 3)
        try:
            await asyncio.wait_for(session.interrupt(force=True), 3)
        finally:
            sink.release.set()
            await asyncio.wait_for(pending, 3)
        assert state.review is None and not store.path.exists()


def test_production_factory_rejects_accidental_text_only_configuration(tmp_path):
    with pytest.raises(ValueError, match="STT and TTS"):
        create_agent_session(
            store=JsonStore(tmp_path / "list.json"), llm=None, stt=None, tts=None
        )


@pytest.mark.asyncio
async def test_failed_write_and_retry_keep_the_same_publication_identity(
    tmp_path, monkeypatch
):
    responses = initial()
    responses["Review it."] = [
        [call("review_records")],
        "Birds has your Illustrated note. Ready to publish?",
    ]
    responses["Yes, publish it."] = [
        [call("publish_records")],
        "Publication failed.",
        [call("publish_records")],
        "Published.",
    ]
    async with opened(tmp_path, responses) as (session, state, store, _model):
        await seed(session, state)
        await run(session, "Review it.")
        write = store.write
        attempts = []

        def fail_once(record):
            attempts.append(json.loads(json.dumps(record)))
            if len(attempts) == 1:
                raise OSError("planned write failure")
            write(record)

        monkeypatch.setattr(store, "write", fail_once)
        await run(session, "Yes, publish it.")
        assert state.publication is None and not store.path.exists()
        await run(session, "Yes, publish it.")
        assert len(attempts) == 2
        assert attempts[0]["publication_id"] == attempts[1]["publication_id"]
        assert attempts[0]["entries"] == attempts[1]["entries"]
        saved = json.loads(store.path.read_text())
        assert saved["publication_id"] == attempts[0]["publication_id"]
        assert len(list(tmp_path.glob("*.json"))) == 1
