import pytest

from app.services import explore as E
from app.services import sets as S

HAO = ord("好")  # 女 + 子
MA = ord("妈")   # 女 + 马
NI = ord("你")   # 亻 + 尔
REN = ord("人")  # no decomposition
LIN = ord("林")  # 木 + 木
NU = ord("女")
ZI = ord("子")
MU = ord("木")

WORD_KEYS = {"id", "simplified", "traditional", "pinyin", "definitions", "added_at"}
COMPONENT_KEYS = {"position", "role", "id", "glyph", "pinyin", "meaning_en"}


def ids(word):
    return [ord(ch) for ch in word]


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


# ---------- fetch_components_by_character_ids ----------

def test_fetch_components_empty_input_skips_the_query():
    assert E.fetch_components_by_character_ids(None, []) == {}


def test_fetch_components_groups_by_character_in_position_order(conn):
    result = E.fetch_components_by_character_ids(conn, [HAO, LIN, REN])
    assert [(c["position"], c["id"]) for c in result[HAO]] == [(0, NU), (1, ZI)]
    assert [c["id"] for c in result[LIN]] == [MU, MU]  # a repeated component is kept
    assert REN not in result                           # no decomposition
    assert set(result[HAO][0]) == COMPONENT_KEYS


# ---------- characters_in_word ----------

def test_characters_in_word_is_unique_and_keeps_first_appearance_order(conn):
    result = E.characters_in_word(conn, ids("妈好妈"))
    assert [(r["id"], r["glyph"]) for r in result] == [(MA, "妈"), (HAO, "好")]
    assert [r["character"]["id"] for r in result] == [MA, HAO]
    assert all(r["is_hanzi"] for r in result)


def test_characters_in_word_includes_the_component_breakdown(conn):
    result = E.characters_in_word(conn, ids("好人林"))
    by_glyph = {r["glyph"]: r["character"]["components"] for r in result}
    assert [(c["glyph"], c["position"]) for c in by_glyph["好"]] == [("女", 0), ("子", 1)]
    assert by_glyph["人"] == []
    assert [c["glyph"] for c in by_glyph["林"]] == ["木", "木"]
    assert set(by_glyph["好"][0]) == COMPONENT_KEYS


def test_characters_in_word_marks_non_hanzi_and_skips_the_database_for_them(conn, monkeypatch):
    sent_to_db = []
    real = E.fetch_characters_by_ids

    def spy(c, character_ids):
        sent_to_db.append(list(character_ids))
        return real(c, character_ids)

    monkeypatch.setattr(E, "fetch_characters_by_ids", spy)

    result = E.characters_in_word(conn, ids("好a1，妈妈"))
    assert [(r["glyph"], r["is_hanzi"]) for r in result] == [
        ("好", True), ("a", False), ("1", False), ("，", False), ("妈", True),
    ]
    assert [r["character"] is None for r in result] == [False, True, True, True, False]
    assert sent_to_db == [[HAO, MA]]  # only unique hanzi code points were queried


def test_characters_in_word_unknown_hanzi_has_no_character(conn, missing_han_id):
    result = E.characters_in_word(conn, [missing_han_id])
    assert result == [
        {"id": missing_han_id, "glyph": chr(missing_han_id), "is_hanzi": True, "character": None}
    ]


def test_characters_in_word_empty_input(conn):
    assert E.characters_in_word(conn, []) == []


# ---------- fetch_words_with_character ----------

def test_words_with_character_returns_only_words_containing_it(conn, user_id, set_id):
    add(conn, user_id, set_id, "你好")
    add(conn, user_id, set_id, "好人")
    add(conn, user_id, set_id, "妈妈")

    rows = E.fetch_words_with_character(conn, user_id, HAO)
    assert sorted(simplified_of(rows)) == ["你好", "好人"]
    assert all(set(r) == WORD_KEYS for r in rows)


def test_words_with_character_finds_characters_without_components(conn, user_id, set_id):
    add(conn, user_id, set_id, "好人")
    assert simplified_of(E.fetch_words_with_character(conn, user_id, REN)) == ["好人"]


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
    other_set = S.create_set(conn, user_id, "second set")["id"]
    add(conn, user_id, set_id, "好人")
    add(conn, user_id, other_set, "好人")

    assert simplified_of(E.fetch_words_with_character(conn, user_id, HAO)) == ["好人"]


def test_words_with_character_counts_a_repeated_character_once(conn, user_id, set_id):
    add(conn, user_id, set_id, "妈妈")  # 妈 appears twice in the word
    assert simplified_of(E.fetch_words_with_character(conn, user_id, MA)) == ["妈妈"]


def test_words_with_character_is_scoped_to_the_user(conn, user_id, other_user_id, set_id):
    other_set = S.create_set(conn, other_user_id, "theirs")["id"]
    add(conn, user_id, set_id, "好人")
    add(conn, other_user_id, other_set, "好吃")

    assert simplified_of(E.fetch_words_with_character(conn, user_id, HAO)) == ["好人"]
    assert simplified_of(E.fetch_words_with_character(conn, other_user_id, HAO)) == ["好吃"]


def test_words_with_character_empty_cases(conn, user_id, set_id, missing_han_id):
    add(conn, user_id, set_id, "妈妈")
    assert E.fetch_words_with_character(conn, user_id, HAO) == []             # no word has it
    assert E.fetch_words_with_character(conn, user_id, missing_han_id) == []  # unknown id


# ---------- fetch_words_with_component ----------

def test_words_with_component_matches_any_character_built_from_it(conn, user_id, set_id):
    add(conn, user_id, set_id, "你好")  # 好 = 女 + 子
    add(conn, user_id, set_id, "妈妈")  # 妈 = 女 + 马
    add(conn, user_id, set_id, "你")    # 亻 + 尔, no 女

    rows = E.fetch_words_with_component(conn, user_id, NU)
    assert sorted(simplified_of(rows)) == ["你好", "妈妈"]
    assert all(set(r) == WORD_KEYS for r in rows)

    # 子 is only in 好
    assert simplified_of(E.fetch_words_with_component(conn, user_id, ZI)) == ["你好"]


def test_words_with_component_includes_the_component_itself(conn, user_id, set_id):
    add(conn, user_id, set_id, "女儿")  # 女 as a whole character
    add(conn, user_id, set_id, "好")
    assert sorted(simplified_of(E.fetch_words_with_component(conn, user_id, NU))) == ["女儿", "好"]


def test_words_with_component_returns_a_word_once_even_if_several_chars_match(conn, user_id, set_id):
    add(conn, user_id, set_id, "好妈")  # two characters, both contain 女
    assert simplified_of(E.fetch_words_with_component(conn, user_id, NU)) == ["好妈"]


def test_words_with_component_counts_a_repeated_component_once(conn, user_id, set_id):
    add(conn, user_id, set_id, "林")  # 木 + 木
    assert simplified_of(E.fetch_words_with_component(conn, user_id, MU)) == ["林"]


def test_words_with_component_returns_distinct_simplified_earliest_first(conn, user_id, set_id):
    add(conn, user_id, set_id, "妈妈", "newer copy")
    older = add(conn, user_id, set_id, "妈妈", "older copy")
    conn.execute(
        "UPDATE flashcard_words SET added_at = now() - interval '1 day' WHERE id = %s",
        (older["id"],),
    )

    rows = E.fetch_words_with_component(conn, user_id, NU)
    assert [r["id"] for r in rows] == [older["id"]]


def test_words_with_component_is_scoped_to_the_user(conn, user_id, other_user_id, set_id):
    other_set = S.create_set(conn, other_user_id, "theirs")["id"]
    add(conn, user_id, set_id, "妈妈")
    add(conn, other_user_id, other_set, "好吃")

    assert simplified_of(E.fetch_words_with_component(conn, user_id, NU)) == ["妈妈"]
    assert simplified_of(E.fetch_words_with_component(conn, other_user_id, NU)) == ["好吃"]


def test_words_with_component_empty_cases(conn, user_id, set_id, missing_han_id):
    add(conn, user_id, set_id, "你")
    assert E.fetch_words_with_component(conn, user_id, NU) == []              # nothing has 女
    assert E.fetch_words_with_component(conn, user_id, missing_han_id) == []  # unknown id
