"""Opt-in ordinary-language checks; scripted tool proposals cannot replace these.

Run with RUN_LIVE_SCOPED=1, MODEL and configured LiveKit Inference credentials.
Each fixed conversation runs once. No tool names are supplied by the caller.
"""

import asyncio
import json
import os

import pytest
from editable_records import JsonStore, create_agent_session
from livekit.agents import inference
from livekit.agents.llm import ChatMessage
from livekit.agents.utils import http_context


def spoken(session):
    return [
        i.text_content
        for i in session.history.items
        if isinstance(i, ChatMessage) and i.role == "assistant"
    ]


async def exercise_scope(session, state, store, turn, name, closed):
    if name == "scope_retraction_and_correction":
        await turn(
            'Make a reading list with "Coastal birds", note "Large print", and "Garden trees", note "Shade". Read it back for my approval, but do not publish.'
        )
        first, second = state.records()
        assert [(r["title"], r["note"]) for r in [first, second]] == [
            ("Coastal birds", "Large print"),
            ("Garden trees", "Shade"),
        ]
        assert state.review is not None and not store.path.exists()
        await turn(
            "No other entries. Keep the two already listed. I am not approving publication yet."
        )
        assert state.records() == [first, second] and not store.path.exists()
        await turn(
            "Do not publish. I assumed the Large print note for Coastal birds; I do not actually know its note, so retract that assumption. Correct Garden trees to Orchard trees and keep its Shade note. Read the corrected list for approval."
        )
        expected = [
            dict(first, note=None),
            dict(second, title="Orchard trees"),
        ]
        assert state.records() == expected
        assert state.review is not None and state.review.text.strip()
        await turn(
            "For Orchard trees, I explicitly want no note after all. Keep Coastal birds and its unknown note as they are. Read back the list before publishing."
        )
        expected[1]["note"] = ""
        assert state.records() == expected and state.review is not None
        assert state.review.text.strip()
    else:
        await turn(
            'My reading list has "Night skies", note "Small print", and "River maps", note "No illustrations". Read it back, but do not publish yet.'
        )
        first, second = state.records()
        assert [(r["title"], r["note"]) for r in [first, second]] == [
            ("Night skies", "Small print"),
            ("River maps", "No illustrations"),
        ]
        await turn(
            "There are no additional readings. Those are the only two. Do not publish yet."
        )
        assert state.records() == [first, second]
        await turn(
            "Remove Night skies only. Keep River maps and its No illustrations note exactly as they are. Read the remaining list for approval."
        )
        expected = [
            {
                "entry_id": second["entry_id"],
                "title": "River maps",
                "note": "No illustrations",
            }
        ]
        assert state.records() == expected and state.review is not None
    assert not store.path.exists()
    approval = "That reflects what I wanted. Release the list, and we can end our conversation."
    await turn(approval)
    await asyncio.wait_for(closed.wait(), 8)
    saved = json.loads(store.path.read_text())
    assert saved["entries"] == expected
    approving = next(
        i
        for i in session.history.items
        if isinstance(i, ChatMessage) and i.id == saved["approved_message_id"]
    )
    assert approving.role == "user" and approving.text_content == approval
    assert saved["publication_id"] in " ".join(spoken(session))
    assert state.closed and state.shutdown_requested


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("RUN_LIVE_SCOPED") != "1",
    reason="Select paid ordinary-language checks explicitly",
)
@pytest.mark.parametrize("name", ["scope_retraction_and_correction", "scoped_removal"])
async def test_ordinary_scope_through_publication_and_close(tmp_path, name):
    store = JsonStore(tmp_path / "publication.json")
    async with http_context.open(), inference.LLM(model=os.environ["MODEL"]) as model:
        session, agent = create_agent_session(
            store=store, llm=model, stt=None, tts=None, text_test=True
        )
        closed = asyncio.Event()
        session.on("close", lambda _event: closed.set())
        async with session:
            await session.start(agent)

            async def turn(text):
                await asyncio.wait_for(session.run(user_input=text), timeout=60)

            await exercise_scope(session, session.userdata, store, turn, name, closed)
