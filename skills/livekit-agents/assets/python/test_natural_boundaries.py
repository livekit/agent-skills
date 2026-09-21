"""Scripted decisions prove runtime mechanics, never language understanding."""

import asyncio
import json

import pytest
from test_editable_records_sdk import (
    assistant_messages,
    call,
    initial,
    opened,
    run,
    seed,
)


@pytest.mark.asyncio
async def test_generated_review_and_model_selected_approval_have_no_phrase_contract(
    tmp_path,
):
    responses = initial()
    review = "Here is Birds, with your Illustrated note. Shall I publish that list?"
    responses["Read the list."] = [[call("review_records")], review]
    approval = "That reflects what I wanted; you have my blessing to release it."
    responses[approval] = [[call("publish_records")], "The list is published."]
    async with opened(tmp_path, responses) as (session, state, store, model):
        entry_id = await seed(session, state)
        await run(session, "Read the list.")
        assert assistant_messages(session)[-1] == review
        assert state.review.text == review
        assert model.calls["Read the list."] == 2
        await run(session, approval)
        saved = json.loads(store.path.read_text())
        assert saved["entries"] == [
            {"entry_id": entry_id, "title": "Birds", "note": "Illustrated"}
        ]
        assert saved["approved_text"] == approval


@pytest.mark.asyncio
async def test_generated_farewell_is_delivered_before_close(tmp_path):
    responses = initial()
    farewell = "I've left your list unpublished. Take care, and enjoy your reading."
    responses["Leave it there and let me go."] = [[call("finish_session")], farewell]
    async with opened(tmp_path, responses) as (session, state, store, model):
        await seed(session, state)
        at_close = []
        closed = asyncio.Event()
        session.on("close", lambda _: at_close.append(assistant_messages(session)[-1]))
        session.on("close", lambda _: closed.set())
        await run(session, "Leave it there and let me go.")

        await asyncio.wait_for(closed.wait(), 3)
        assert at_close == [farewell]
        assert state.closed and not store.path.exists()
        assert model.calls["Leave it there and let me go."] == 2
