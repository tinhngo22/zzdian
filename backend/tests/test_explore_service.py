import pytest

from app.services import explore as E
from app.services import sets as S

HAO = ord("好")  # main radical 38 (女)
MA = ord("妈")   # main radical 38 (女)
NI = ord("你")   # main radical 9 (人)

WORD_KEYS = {"id", "simplified", "traditional", "pinyin", "definitions", "added_at"}


def add(conn, user_id, set_id, simplified, definitions=None):
    return S.add_word(conn, user_id, set_id, simplified, None, None, definitions)


def simplified_of(rows):
    return [r["simplified"] for r in rows]


# ---------- is_hanzi ----------

@pytest.mark.parametrize(
    "ch",
    ["好", "你", "\u3400", "\u9fff", "\uf900", "\U00020000"],  # incl. Ext A, B, compat
)
def test_is_hanzi_true(ch):
    assert E.is_hanzi(ch)


@pytest.mark.parametrize(
    "ch",
    ["a", "Z", "1", " ", ",", "，", "。", "あ", "한", "\u2f25", "\u2e80"],
    # letters, digits, punctuation, kana, hangul, Kangxi radical + radical supplement
)
def test_is_hanzi_false(ch):
    assert not E.is_hanzi(ch)


# ---------- fetch_characters_by_ids ----------

def test_fetch_characters_by_ids_empty_input_skips_the_query():
    # conn=None would blow up if a query were attempted
    assert E.fetch_characters_by_ids(None, []) == []


def test_fetch_characters_by_ids_returns_rows(conn):
    rows = E.fetch_characters_by_ids(conn, [HAO, MA])
    assert {r["id"] for r in rows} == {HAO, MA}
    hao = next(r for r in rows if r["id"] == HAO)
    assert hao["glyph"] == "好"
    assert hao["main_radical_id"] == 38
    assert set(hao) == {"id", "glyph", "pinyin", "meaning_en", "stroke_count", "main_radical_id"}


def test_fetch_characters_by_ids_ignores_unknown_ids(conn, missing_han_id):
    rows = E.fetch_characters_by_ids(conn, [HAO, missing_han_id])
    assert [r["id"] for r in rows] == [HAO]


# ---------- characters_in_word ----------

def test_characters_in_word_is_unique_and_keeps_first_appearance_order(conn):
    result = E.characters_in_word(conn, "妈好妈")
    assert [r["glyph"] for r in result] == ["妈", "好"]
    assert [r["character"]["id"] for r in result] == [MA, HAO]
    assert all(r["is_hanzi"] for r in result)


def test_characters_in_word_marks_non_hanzi_and_skips_the_database_for_them(conn, monkeypatch):
    sent_to_db = []
    real = E.fetch_characters_by_ids

    def spy(c, ids):
        sent_to_db.append(list(ids))
        return real(c, ids)

    monkeypatch.setattr(E, "fetch_characters_by_ids", spy)

    result = E.characters_in_word(conn, "好a1，妈妈")
    assert [(r["glyph"], r["is_hanzi"]) for r in result] == [
        ("好", True), ("a", False), ("1", False), ("，", False), ("妈", True),
    ]
    assert [r["character"] is None for r in result] == [False, True, True, True, False]
    assert sent_to_db == [[HAO, MA]]  # only unique hanzi code points were queried


def test_characters_in_word_unknown_hanzi_has_no_character(conn, missing_han_id):
    result = E.characters_in_word(conn, chr(missing_han_id))
    assert result == [{"glyph": chr(missing_han_id), "is_hanzi": True, "character": None}]


def test_characters_in_word_empty_string(conn):
    assert E.characters_in_word(conn, "") == []


# ---------- fetch_words_with_character ----------

def test_words_with_character_returns_only_words_containing_it(conn, user_id, set_id):
    add(conn, user_id, set_id, "你好")
    add(conn, user_id, set_id, "好人")
    add(conn, user_id, set_id, "妈妈")

    rows = E.fetch_words_with_character(conn, user_id, HAO)
    assert sorted(simplified_of(rows)) == ["你好", "好人"]
    assert all(set(r) == WORD_KEYS for r in rows)


def test_words_with_character_returns_distinct_simplified_earliest_first(conn, user_id, set_id):
    first = add(conn, user_id, set_id, "好人", "newer copy")
    older = add(conn, user_id, set_id, "好人", "older copy")
    conn.execute(
        "UPDATE flashcard_words SET added_at = now() - interval '1 day' WHERE id = %s",
        (older["id"],),
    )

    rows = E.fetch_words_with_character(conn, user_id, HAO)
    assert len(rows) == 1
    assert rows[0]["id"] == older["id"]  # earliest-added copy wins
    assert rows[0]["id"] != first["id"]


def test_words_with_character_dedupes_across_sets(conn, user_id, set_id):
    from app.services import sets

    other_set = sets.create_set(conn, user_id, "second set")["id"]
    add(conn, user_id, set_id, "好人")
    add(conn, user_id, other_set, "好人")

    assert simplified_of(E.fetch_words_with_character(conn, user_id, HAO)) == ["好人"]


def test_words_with_character_counts_a_repeated_character_once(conn, user_id, set_id):
    add(conn, user_id, set_id, "妈妈")  # 妈 appears twice in the word
    assert simplified_of(E.fetch_words_with_character(conn, user_id, MA)) == ["妈妈"]


def test_words_with_character_is_scoped_to_the_user(conn, user_id, other_user_id, set_id):
    from app.services import sets

    other_set = sets.create_set(conn, other_user_id, "theirs")["id"]
    add(conn, user_id, set_id, "好人")
    add(conn, other_user_id, other_set, "好吃")

    assert simplified_of(E.fetch_words_with_character(conn, user_id, HAO)) == ["好人"]
    assert simplified_of(E.fetch_words_with_character(conn, other_user_id, HAO)) == ["好吃"]


def test_words_with_character_empty_cases(conn, user_id, set_id, missing_han_id):
    add(conn, user_id, set_id, "妈妈")
    assert E.fetch_words_with_character(conn, user_id, HAO) == []         # no word has it
    assert E.fetch_words_with_character(conn, user_id, missing_han_id) == []  # unknown id


# ---------- fetch_words_with_same_radical ----------

def test_words_with_same_radical_matches_any_character_with_that_radical(conn, user_id, set_id):
    add(conn, user_id, set_id, "你好")  # has 好 (女)
    add(conn, user_id, set_id, "妈妈")  # has 妈 (also 女) but not 好
    add(conn, user_id, set_id, "你")    # only 人

    rows = E.fetch_words_with_same_radical(conn, user_id, HAO)
    assert sorted(simplified_of(rows)) == ["你好", "妈妈"]
    assert all(set(r) == WORD_KEYS for r in rows)

    # and the other way round: 你 (人) only matches words with a 人-radical character
    assert sorted(simplified_of(E.fetch_words_with_same_radical(conn, user_id, NI))) == ["你", "你好"]


def test_words_with_same_radical_returns_a_word_once_even_if_several_chars_match(conn, user_id, set_id):
    add(conn, user_id, set_id, "好妈")  # two characters, both 女
    assert simplified_of(E.fetch_words_with_same_radical(conn, user_id, HAO)) == ["好妈"]


def test_words_with_same_radical_returns_distinct_simplified_earliest_first(conn, user_id, set_id):
    add(conn, user_id, set_id, "妈妈", "newer copy")
    older = add(conn, user_id, set_id, "妈妈", "older copy")
    conn.execute(
        "UPDATE flashcard_words SET added_at = now() - interval '1 day' WHERE id = %s",
        (older["id"],),
    )

    rows = E.fetch_words_with_same_radical(conn, user_id, HAO)
    assert [r["id"] for r in rows] == [older["id"]]


def test_words_with_same_radical_is_scoped_to_the_user(conn, user_id, other_user_id, set_id):
    from app.services import sets

    other_set = sets.create_set(conn, other_user_id, "theirs")["id"]
    add(conn, user_id, set_id, "妈妈")
    add(conn, other_user_id, other_set, "好吃")

    assert simplified_of(E.fetch_words_with_same_radical(conn, user_id, HAO)) == ["妈妈"]
    assert simplified_of(E.fetch_words_with_same_radical(conn, other_user_id, HAO)) == ["好吃"]


def test_words_with_same_radical_empty_cases(conn, user_id, set_id, missing_han_id, no_radical_id):
    add(conn, user_id, set_id, "你")
    assert E.fetch_words_with_same_radical(conn, user_id, HAO) == []              # nothing shares 女
    assert E.fetch_words_with_same_radical(conn, user_id, missing_han_id) == []   # unknown id
    assert E.fetch_words_with_same_radical(conn, user_id, no_radical_id) == []    # no main radical
