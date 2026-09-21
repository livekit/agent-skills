"""The operation's scope must survive the complete review/publication path."""

import json

import pytest
from editable_records import JsonStore, NewEntry, RecordBook, RefusedError


def test_batch_addition_is_atomic_and_preserves_previous_entries():
    book = RecordBook()
    existing = book.add("Birds", "Large print")["entry"]
    with pytest.raises(RefusedError):
        book.add_many([NewEntry("Trees", "Shade"), NewEntry(" ", "Invalid")])
    assert book.records() == [existing]
    result = book.add_many([NewEntry("Trees", "Shade"), NewEntry("Stars")])
    assert [(r["title"], r["note"]) for r in result["entries"]] == [
        ("Birds", "Large print"),
        ("Trees", "Shade"),
        ("Stars", None),
    ]
    assert result["entries"][0] == existing
    assert len({r["entry_id"] for r in result["entries"]}) == 3


def test_no_additional_entries_preserves_records_and_existing_review(tmp_path):
    book = RecordBook(clock=lambda: 10.0)
    first = book.add("Coastal birds", "Large print")["entry"]
    second = book.add("Garden trees", "Shade")["entry"]
    book.observe_user("review-request", "Read these two entries.", 9)
    book.review_completed(book.version, "readback", "Fixture review delivered.")
    receipt = book.review
    before = book.records()
    result = book.confirm_entries()
    assert result["entries"] == before == [first, second]
    assert result["changed"] is False
    assert book.review is receipt
    book.observe_user("approval", "Yes, publish it.", 11)
    book.publish(JsonStore(tmp_path / "list.json"))
    assert json.loads((tmp_path / "list.json").read_text())["entries"] == [
        first,
        second,
    ]


def test_empty_answer_cannot_erase_an_existing_collection():
    book = RecordBook()
    entry = book.add("Night skies", "Large print")["entry"]
    before = book.version
    with pytest.raises(RefusedError, match="confirm_entries"):
        book.empty()
    assert book.records() == [entry]
    assert book.version == before
    empty = RecordBook()
    assert empty.empty()["entries"] == []
    assert empty.entries == {}


def test_retraction_absence_and_partial_correction_preserve_other_facts(tmp_path):
    book = RecordBook(clock=lambda: 10.0)
    first = book.add("Coastal birds", "Large print")["entry"]
    second = book.add("Garden trees", "Shade")["entry"]
    book.observe_user("first-review", "Read them.", 9)
    book.review_completed(book.version, "old-review", "Fixture review delivered.")
    book.observe_user(
        "correction", "Retract the first note; correct the second title.", 11
    )
    book.note_unknown(first["entry_id"])
    book.patch(second["entry_id"], title="Orchard trees")
    assert book.review is None
    expected = [dict(first, note=None), dict(second, title="Orchard trees")]
    assert book.records() == expected
    with pytest.raises(RefusedError):
        book.publish(JsonStore(tmp_path / "list.json"))
    book.clear_note(second["entry_id"])
    expected[1]["note"] = ""
    book.confirm_entries()
    book.clock = lambda: 12.0
    text = "Fixture review delivered."
    assert [r["note"] for r in book.review_data()["entries"]] == [None, ""]
    book.review_completed(book.version, "corrected-review", text)
    book.observe_user("final-approval", "Yes, publish it.", 13)
    book.publish(JsonStore(tmp_path / "list.json"))
    saved = json.loads((tmp_path / "list.json").read_text())
    assert saved["entries"] == expected
    assert saved["approved_message_id"] == "final-approval"
    assert saved["review_speech_id"] == "corrected-review"


def test_removing_one_entry_preserves_another_and_bad_target_cannot_add():
    book = RecordBook()
    first = book.add("Birds", "Large print")["entry"]
    second = book.add("Trees", "Shade")["entry"]
    with pytest.raises(RefusedError):
        book.patch("not-an-issued-id", title="Flowers")
    assert book.records() == [first, second]
    book.remove(first["entry_id"])
    assert book.records() == [second]
