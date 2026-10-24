from app.services import dictionary as D

HAO = ord("好")  # 22909, main radical 38 (女)
NV = ord("女")
ZI = ord("子")
LIN = ord("林")
MU = ord("木")


def test_fetch_character_returns_the_row(conn):
    char = D.fetch_character(conn, HAO)
    assert char["id"] == HAO
    assert char["glyph"] == "好"
    assert char["pinyin"] == ["hǎo"]
    assert char["stroke_count"] == 6
    assert char["main_radical_id"] == 38
    assert set(char) == {"id", "glyph", "pinyin", "meaning_en", "stroke_count", "main_radical_id"}


def test_fetch_character_unknown_is_none(conn, missing_han_id):
    assert D.fetch_character(conn, missing_han_id) is None


def test_fetch_radical(conn):
    radical = D.fetch_radical(conn, 38)
    assert radical["glyph"] == "女"
    assert radical["meaning_en"] == "WOMAN"


def test_fetch_radical_unknown_is_none(conn):
    assert D.fetch_radical(conn, 9999) is None


def test_fetch_components_are_in_order(conn):
    components = D.fetch_components(conn, HAO)  # 好 = 女 + 子
    assert [c["position"] for c in components] == [0, 1]
    assert [c["id"] for c in components] == [NV, ZI]
    assert [c["glyph"] for c in components] == ["女", "子"]


def test_fetch_components_can_repeat_a_component(conn):
    components = D.fetch_components(conn, LIN)  # 林 = 木 + 木
    assert [c["id"] for c in components] == [MU, MU]
    assert [c["position"] for c in components] == [0, 1]


def test_fetch_components_of_an_unknown_id_is_empty(conn):
    assert D.fetch_components(conn, 999_999_999) == []
