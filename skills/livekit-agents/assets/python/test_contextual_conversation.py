"""Real-model interpretation; expected effects, not lists of accepted phrases."""

import asyncio
import json
import os

import pytest
from editable_records import JsonStore, create_agent_session
from livekit.agents import inference
from livekit.agents.llm import ChatMessage
from livekit.agents.utils import http_context


async def exercise_context(session, state, store, turn, name):
    await turn(
        'Put "Do not wait" on my reading list, with note "For Sam". Read it back before publishing.'
    )
    original = state.records()
    assert [(r["title"], r["note"]) for r in original] == [("Do not wait", "For Sam")]
    assert state.review is not None and not store.path.exists()
    if name == "agreement_to_review":
        await turn("Yes.")
    elif name == "agreement_to_another_question":
        await turn(
            "Before deciding about publication, ask me whether I have another entry to add."
        )
        assert not store.path.exists()
        await turn("Yes.")
        assert not store.path.exists() and state.records() == original
        await turn(
            "On reflection, keep just the original entry. You have my permission to publish that list as reviewed."
        )
    elif name == "correction_with_conditional_approval":
        old = state.review
        await turn(
            "I approve once you change the note to For Jo. Read the revised list to me first."
        )
        assert not store.path.exists()
        assert state.records() == [dict(original[0], note="For Jo")]
        assert state.review is not None and state.review.version > old.version
        await turn("You have my blessing to release the revised list.")
        original[0]["note"] = "For Jo"
    else:
        answer = await turn(
            'If I said "go ahead and publish", would that make this public? I am asking what happens, not giving permission.'
        )
        assert not store.path.exists() and state.records() == original
        async with inference.LLM(model=os.environ["MODEL"]) as judge:
            await answer.expect.contains_message(role="assistant").judge(
                judge,
                intent="Answers the user's hypothetical question while making clear that no publication happened. Speaks naturally to a person without exposing internal function names, code, tool syntax, or a prescribed command phrase the person must use.",
            )
        await turn("Leave it unpublished while I think.")
        assert not store.path.exists()
        await turn("I have decided: release the list exactly as you reviewed it.")
    saved = json.loads(store.path.read_text())
    assert saved["entries"] == original
    assert saved["approved_message_id"] == state.latest_user.message_id
    assert any(
        saved["publication_id"] in (item.text_content or "")
        for item in session.history.items
        if isinstance(item, ChatMessage) and item.role == "assistant"
    )


CASES = [
    "agreement_to_review",
    "agreement_to_another_question",
    "correction_with_conditional_approval",
    "quoted_instruction_and_refusal",
]


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("RUN_LIVE_SCOPED") != "1",
    reason="Select paid ordinary-language checks explicitly",
)
@pytest.mark.parametrize("name", CASES)
async def test_contextual_interpretation(tmp_path, name):
    store = JsonStore(tmp_path / "publication.json")
    async with http_context.open(), inference.LLM(model=os.environ["MODEL"]) as model:
        session, agent = create_agent_session(
            store=store, llm=model, stt=None, tts=None, text_test=True
        )
        async with session:
            await session.start(agent)

            async def turn(text):
                return await asyncio.wait_for(session.run(user_input=text), timeout=60)

            await exercise_context(session, session.userdata, store, turn, name)
