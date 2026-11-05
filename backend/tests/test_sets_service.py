from uuid import uuid4

import psycopg
import pytest

from app.db import fetch_all
from app.services import sets as S

def add(conn, user_id, set_id, simplified, traditional=None, pinyin=None, definitions=None):
    return S.add_word(conn, user_id, set_id, simplified, traditional, pinyin, definitions)


def explore_rows(conn, word_id):
    return fetch_all(
        conn,
        "SELECT user_id, component_id, character_id, word_id FROM explore "
        "WHERE word_id = %s ORDER BY character_id, component_id",
        (word_id,),
    )


def pairs(rows):
    """(character, component) glyph pairs, for readable assertions."""
    return {(chr(r["character_id"]), chr(r["component_id"])) for r in rows}


def count(conn, table, **where):
    clause = " AND ".join(f"{k} = %s" for k in where)
    return conn.execute(f"SELECT count(*) FROM {table} WHERE {clause}", tuple(where.values())).fetchone()[0]


def set_added_at(conn, word_id, days_ago):
    conn.execute(
        "UPDATE flashcard_words SET added_at = now() - make_interval(days => %s) WHERE id = %s",
        (days_ago, word_id),
    )


# ---------- sets ----------

def test_create_set(conn, user_id):
    row = S.create_set(conn, user_id, "HSK 1")
    assert set(row) == {"id", "name", "created_at"}
    assert row["name"] == "HSK 1"
    assert count(conn, "flashcard_sets", id=row["id"], user_id=user_id) == 1


def test_set_exists_for_user(conn, user_id, other_user_id, set_id):
    assert S.set_exists_for_user(conn, set_id, user_id)
    assert not S.set_exists_for_user(conn, set_id, other_user_id)  # not their set
    assert not S.set_exists_for_user(conn, uuid4(), user_id)       # unknown set


def test_list_sets_empty_for_new_user(conn, user_id):
    assert S.list_sets(conn, user_id) == []


def test_list_sets_orders_by_creation_and_counts_words(conn, user_id):
    older = S.create_set(conn, user_id, "older")["id"]
    newer = S.create_set(conn, user_id, "newer")["id"]
    conn.execute(
        "UPDATE flashcard_sets SET created_at = now() - interval '1 day' WHERE id = %s", (older,)
    )
    add(conn, user_id, newer, "你好")
    add(conn, user_id, newer, "好人")

    rows = S.list_sets(conn, user_id)
    assert [(r["name"], r["word_count"]) for r in rows] == [("older", 0), ("newer", 2)]
    assert set(rows[0]) == {"id", "name", "created_at", "word_count"}


def test_list_sets_only_shows_the_users_own_sets(conn, user_id, other_user_id):
    S.create_set(conn, user_id, "mine")
    S.create_set(conn, other_user_id, "theirs")
    assert [r["name"] for r in S.list_sets(conn, user_id)] == ["mine"]


def test_rename_set(conn, user_id, set_id):
    row = S.rename_set(conn, user_id, set_id, "renamed")
    assert row["id"] == set_id
    assert row["name"] == "renamed"
    assert conn.execute("SELECT name FROM flashcard_sets WHERE id = %s", (set_id,)).fetchone()[0] == "renamed"


def test_rename_set_of_another_user_or_unknown_set_is_none(conn, user_id, other_user_id, set_id):
    assert S.rename_set(conn, other_user_id, set_id, "hijacked") is None
    assert S.rename_set(conn, user_id, uuid4(), "x") is None
    assert conn.execute("SELECT name FROM flashcard_sets WHERE id = %s", (set_id,)).fetchone()[0] == "test set"


def test_delete_set(conn, user_id, set_id):
    assert S.delete_set(conn, user_id, set_id) is True
    assert not S.set_exists_for_user(conn, set_id, user_id)
    assert S.delete_set(conn, user_id, set_id) is False  # already gone


def test_delete_set_of_another_user_is_refused(conn, user_id, other_user_id, set_id):
    assert S.delete_set(conn, other_user_id, set_id) is False
    assert S.set_exists_for_user(conn, set_id, user_id)


def test_delete_set_cascades_to_its_words_and_explore_rows(conn, user_id, set_id):
    word = add(conn, user_id, set_id, "你好")
    assert explore_rows(conn, word["id"])

    assert S.delete_set(conn, user_id, set_id) is True
    assert count(conn, "flashcard_words", set_id=set_id) == 0
    assert explore_rows(conn, word["id"]) == []


# ---------- add_word ----------

def test_add_word_returns_and_stores_the_word(conn, user_id, set_id):
    word = add(conn, user_id, set_id, "你好", "你好", "nǐ hǎo", "hello")
    assert set(word) == {"id", "simplified", "traditional", "pinyin", "definitions", "added_at"}
    assert (word["simplified"], word["traditional"], word["pinyin"], word["definitions"]) == (
        "你好", "你好", "nǐ hǎo", "hello",
    )
    stored = conn.execute(
        "SELECT user_id, set_id FROM flashcard_words WHERE id = %s", (word["id"],)
    ).fetchone()
    assert stored == (user_id, set_id)


def test_add_word_optional_fields_can_be_none(conn, user_id, set_id):
    word = add(conn, user_id, set_id, "好")
    assert (word["traditional"], word["pinyin"], word["definitions"]) == (None, None, None)


def test_add_word_links_each_character_with_itself_and_its_components(conn, user_id, set_id):
    word = add(conn, user_id, set_id, "你好")
    rows = explore_rows(conn, word["id"])
    assert pairs(rows) == {
        ("你", "你"), ("你", "亻"), ("你", "尔"),
        ("好", "好"), ("好", "女"), ("好", "子"),
    }
    assert all(r["user_id"] == user_id and r["word_id"] == word["id"] for r in rows)


def test_add_word_links_a_repeated_character_once(conn, user_id, set_id):
    word = add(conn, user_id, set_id, "妈妈")
    assert pairs(explore_rows(conn, word["id"])) == {("妈", "妈"), ("妈", "女"), ("妈", "马")}
    assert len(explore_rows(conn, word["id"])) == 3


def test_add_word_links_a_repeated_component_once(conn, user_id, set_id):
    word = add(conn, user_id, set_id, "林")  # 木 + 木
    assert pairs(explore_rows(conn, word["id"])) == {("林", "林"), ("林", "木")}
    assert len(explore_rows(conn, word["id"])) == 2


def test_add_word_links_a_character_without_components_to_itself(conn, user_id, set_id, no_components_id):
    word = add(conn, user_id, set_id, chr(no_components_id))
    rows = explore_rows(conn, word["id"])
    assert [(r["character_id"], r["component_id"]) for r in rows] == [
        (no_components_id, no_components_id)
    ]


def test_add_word_skips_non_hanzi_and_unknown_characters(conn, user_id, set_id, missing_han_id):
    word = add(conn, user_id, set_id, f"A1，{chr(missing_han_id)}")
    assert explore_rows(conn, word["id"]) == []


def test_add_word_twice_creates_two_independent_words(conn, user_id, set_id):
    a = add(conn, user_id, set_id, "好人")
    b = add(conn, user_id, set_id, "好人")
    assert a["id"] != b["id"]
    assert pairs(explore_rows(conn, a["id"])) == pairs(explore_rows(conn, b["id"])) == {
        ("好", "好"), ("好", "女"), ("好", "子"), ("人", "人"),
    }


def test_link_word_characters_rejects_a_user_that_does_not_own_the_word(conn, user_id, other_user_id, set_id):
    word = add(conn, user_id, set_id, "好")
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with conn.transaction():  # savepoint, so the test connection stays usable
            S.link_word_characters(conn, other_user_id, word["id"], "你")


# ---------- add_words ----------

def test_add_words_stores_them_in_order_with_optional_fields(conn, user_id, set_id):
    words = [
        {"simplified": "三", "traditional": None, "pinyin": "sān", "definitions": "three"},
        {"simplified": "一", "traditional": None, "pinyin": None, "definitions": None},
        {"simplified": "说话", "traditional": "說話", "pinyin": "shuō huà", "definitions": "to speak\nto talk"},
    ]
    rows = S.add_words(conn, user_id, set_id, words)

    assert [r["simplified"] for r in rows] == ["三", "一", "说话"]
    assert set(rows[0]) == {"id", "simplified", "traditional", "pinyin", "definitions", "added_at"}
    assert (rows[2]["traditional"], rows[2]["pinyin"], rows[2]["definitions"]) == (
        "說話", "shuō huà", "to speak\nto talk",
    )
    assert (rows[1]["pinyin"], rows[1]["definitions"]) == (None, None)
    listed = S.list_words(conn, user_id, set_id, limit=10, offset=0)
    assert [r["simplified"] for r in listed] == ["三", "一", "说话"]  # import order, not text order


def test_add_words_links_each_word_in_explore(conn, user_id, set_id):
    a, b = S.add_words(
        conn, user_id, set_id,
        [{"simplified": "你好"}, {"simplified": "林"}],
    )
    assert pairs(explore_rows(conn, a["id"])) == {
        ("你", "你"), ("你", "亻"), ("你", "尔"),
        ("好", "好"), ("好", "女"), ("好", "子"),
    }
    assert pairs(explore_rows(conn, b["id"])) == {("林", "林"), ("林", "木")}


def test_add_words_empty_list_does_nothing(conn, user_id, set_id):
    assert S.add_words(conn, user_id, set_id, []) == []
    assert S.count_words(conn, user_id, set_id) == 0


# ---------- count_words / list_words ----------

def test_count_and_list_words(conn, user_id, set_id):
    for simplified, days_ago in [("三", 1), ("一", 3), ("二", 2)]:
        word = add(conn, user_id, set_id, simplified)
        set_added_at(conn, word["id"], days_ago)

    assert S.count_words(conn, user_id, set_id) == 3
    rows = S.list_words(conn, user_id, set_id, limit=10, offset=0)
    assert [r["simplified"] for r in rows] == ["一", "二", "三"]  # oldest first
    assert set(rows[0]) == {"id", "simplified", "traditional", "pinyin", "definitions", "added_at"}


def test_list_words_pagination(conn, user_id, set_id):
    for i, simplified in enumerate(["一", "二", "三"]):
        set_added_at(conn, add(conn, user_id, set_id, simplified)["id"], 10 - i)

    page = lambda limit, offset: [
        r["simplified"] for r in S.list_words(conn, user_id, set_id, limit, offset)
    ]
    assert page(2, 0) == ["一", "二"]
    assert page(2, 2) == ["三"]
    assert page(2, 5) == []


def test_words_are_only_visible_to_the_owner_of_the_set(conn, user_id, other_user_id, set_id):
    add(conn, user_id, set_id, "好")
    assert S.count_words(conn, other_user_id, set_id) == 0
    assert S.list_words(conn, other_user_id, set_id, 10, 0) == []


def test_words_of_different_sets_do_not_mix(conn, user_id, set_id):
    other_set = S.create_set(conn, user_id, "second")["id"]
    add(conn, user_id, set_id, "一")
    add(conn, user_id, other_set, "二")
    assert [r["simplified"] for r in S.list_words(conn, user_id, set_id, 10, 0)] == ["一"]
    assert S.count_words(conn, user_id, other_set) == 1


# ---------- remove_word ----------

def test_remove_word_deletes_it_and_its_explore_rows(conn, user_id, set_id):
    keep = add(conn, user_id, set_id, "好人")
    gone = add(conn, user_id, set_id, "你好")

    assert S.remove_word(conn, user_id, set_id, gone["id"]) is True
    assert count(conn, "flashcard_words", id=gone["id"]) == 0
    assert explore_rows(conn, gone["id"]) == []
    assert count(conn, "flashcard_words", id=keep["id"]) == 1   # other words untouched
    assert pairs(explore_rows(conn, keep["id"])) == {
        ("好", "好"), ("好", "女"), ("好", "子"), ("人", "人"),
    }


def test_remove_word_returns_false_when_it_is_not_in_that_users_set(conn, user_id, other_user_id, set_id):
    word = add(conn, user_id, set_id, "好")
    other_set = S.create_set(conn, user_id, "second")["id"]

    assert S.remove_word(conn, other_user_id, set_id, word["id"]) is False  # not their word
    assert S.remove_word(conn, user_id, other_set, word["id"]) is False     # wrong set
    assert S.remove_word(conn, user_id, set_id, uuid4()) is False           # unknown word
    assert count(conn, "flashcard_words", id=word["id"]) == 1
