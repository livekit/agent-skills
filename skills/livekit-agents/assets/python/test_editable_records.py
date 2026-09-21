"""Record semantics: independent expectations through real mutation methods."""

from types import SimpleNamespace

import pytest
from editable_records import JsonStore, NewEntry, RecordBook, RecordsAgent, RefusedError


def test_correction_preserves_identity_and_unrelated_note():
    book = RecordBook()
    result = book.add("Coastal birds", "Large print")
    key = result["entry"]["entry_id"]
    changed = book.patch(key, title="Forest birds")
    assert changed["changed"]
    assert book.records() == [
        {"entry_id": key, "title": "Forest birds", "note": "Large print"}
    ]


def test_rename_then_note_correction_keeps_one_record():
    book = RecordBook()
    key = book.add("Birds", "Large print")["entry"]["entry_id"]
    book.patch(key, title="Local birds")
    book.patch(key, note="Illustrated")
    assert book.records() == [
        {"entry_id": key, "title": "Local birds", "note": "Illustrated"}
    ]


def test_same_titles_have_different_identity():
    book = RecordBook()
    first = book.add("Birds")["entry"]["entry_id"]
    second = book.add("Birds")["entry"]["entry_id"]
    book.patch(second, note="For a child")
    assert first != second
    assert book.records()[0]["note"] is None
    assert book.records()[1]["note"] == "For a child"


def test_omitted_and_null_patch_fields_preserve_existing_values():
    book = RecordBook()
    key = book.add("Birds", "Illustrated")["entry"]["entry_id"]
    receipt = object()
    book.review = receipt
    version = book.version
    assert book.patch(key, title=None, note=None)["changed"] is False
    assert book.patch(key, title="Birds", note="Illustrated")["changed"] is False
    assert book.review is receipt and book.version == version


def test_unknown_and_explicitly_empty_notes_are_distinct():
    book = RecordBook()
    key = book.add("Birds")["entry"]["entry_id"]
    assert book.records()[0]["note"] is None
    book.clear_note(key)
    assert book.records()[0]["note"] == ""
    book.note_unknown(key)
    assert book.records()[0]["note"] is None


@pytest.mark.parametrize("title", ["", "   "])
def test_failed_patch_preserves_every_field_and_review(title):
    book = RecordBook()
    key = book.add("Birds", "Illustrated")["entry"]["entry_id"]
    before, version, receipt = book.records(), book.version, object()
    book.review = receipt
    with pytest.raises(RefusedError):
        book.patch(key, title=title, note="Large print")
    assert (
        book.records() == before and book.version == version and book.review is receipt
    )


def test_missing_target_cannot_add_or_remove_something_else():
    book = RecordBook()
    book.add("Birds")
    before = book.records()
    with pytest.raises(RefusedError):
        book.patch("not-a-real-id", title="Trees")
    with pytest.raises(RefusedError):
        book.remove("not-a-real-id")
    assert book.records() == before


def test_removal_targets_one_record_and_keeps_other_record():
    book = RecordBook()
    first = book.add("Birds")["entry"]["entry_id"]
    second = book.add("Trees", "Illustrated")["entry"]["entry_id"]
    book.remove(first)
    assert book.records() == [
        {"entry_id": second, "title": "Trees", "note": "Illustrated"}
    ]


def test_unanswered_collection_is_not_explicitly_empty():
    book = RecordBook()
    with pytest.raises(RefusedError):
        book.review_data()
    book.empty()
    assert book.review_data()["entries"] == []


def test_results_are_copies_and_report_next_valid_action():
    book = RecordBook()
    result = book.add("Birds", "Illustrated")
    result["entry"]["title"] = "Injected"
    result["entries"][0]["note"] = "Injected"
    assert book.records()[0]["title"] == "Birds"
    assert book.records()[0]["note"] == "Illustrated"
    assert "review_records" in result["next_action"]


@pytest.mark.asyncio
async def test_actual_tool_patch_preserves_unrelated_values(tmp_path):
    book = RecordBook()
    agent = RecordsAgent(JsonStore(tmp_path / "list.json"))
    ctx = SimpleNamespace(userdata=book)
    result = await agent.add_entries(ctx, entries=[NewEntry("Birds", "Illustrated")])
    key = result["added"][0]["entry_id"]
    await agent.correct_entry(ctx, entry_id=key, title="Trees", note=None)
    assert book.records() == [
        {"entry_id": key, "title": "Trees", "note": "Illustrated"}
    ]


def test_atomic_store_failure_preserves_existing_file(tmp_path, monkeypatch):
    path = tmp_path / "list.json"
    store = JsonStore(path)
    store.write({"old": True})
    before = path.read_bytes()

    def fail(*args):
        raise OSError("replace unavailable")

    monkeypatch.setattr("editable_records.os.replace", fail)
    with pytest.raises(OSError):
        store.write({"new": True})
    assert path.read_bytes() == before
    assert len(list(tmp_path.iterdir())) == 1
