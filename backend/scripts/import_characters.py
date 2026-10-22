from __future__ import annotations
import json

from app.db import get_conn
from scripts.utils import MMAH_FILE
from scripts.utils import first_int, load_unihan

UNIHAN_FIELDS = {"kMandarin", "kTotalStrokes", "kRSUnicode", "kDefinition"}

# Ideographic Description Characters: they describe layout, they are not components.
IDS_CHARS = set("⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻")

CHAR_SQL = """
INSERT INTO characters (id, glyph, pinyin, meaning_en, stroke_count, main_radical_id)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (id) DO UPDATE SET
    pinyin = EXCLUDED.pinyin,
    meaning_en = EXCLUDED.meaning_en,
    stroke_count = EXCLUDED.stroke_count,
    main_radical_id = EXCLUDED.main_radical_id
"""

COMPONENT_SQL = """
INSERT INTO character_components (character_id, position, component_id, role)
VALUES (%s, %s, %s, %s)
"""


def is_han(ch: str) -> bool:
    cp = ord(ch)
    return (
        0x3400 <= cp <= 0x4DBF      # Extension A
        or 0x4E00 <= cp <= 0x9FFF   # main block
        or 0xF900 <= cp <= 0xFAFF   # compatibility ideographs
        or 0x20000 <= cp <= 0x2FA1F # extensions B and beyond
    )


def load_mmah() -> dict[str, dict]:
    # load mmah into {"好"：{info from mmah}, ...} form
    entries = {}
    with MMAH_FILE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entry = json.loads(line)
                entries[entry["character"]] = entry
    return entries


def extract_components(glyph: str, entry: dict) -> list[tuple[int, str, str]]:
    """Return [(position, component_glyph, role), ...] for one character."""
    decomposition = entry.get("decomposition", "")
    parts = [c for c in decomposition if c not in IDS_CHARS and c != "？" and c != glyph]

    etymology = entry.get("etymology") or {}
    semantic = etymology.get("semantic")
    phonetic = etymology.get("phonetic")

    result = []
    for position, part in enumerate(parts):
        if part == semantic:
            role = "semantic"
        elif part == phonetic:
            role = "phonetic"
        else:
            role = "component"
        result.append((position, part, role))
    return result


def main():
    uni = load_unihan(UNIHAN_FIELDS)
    mmah = load_mmah()
    print(f"unihan: {len(uni)} code points, makemeahanzi: {len(mmah)} entries")

    with get_conn() as conn:
        # get every Han character that appears in a word
        glyphs: set[str] = set()
        for simplified, traditional in conn.execute(
            "SELECT simplified, traditional FROM words"
        ):
            glyphs.update(ch for ch in simplified + traditional if is_han(ch))
        print(f"{len(glyphs)} distinct characters appear in words")

        # BFS, extract components from word list first, then components extracted from those words
        components: dict[str, list[tuple[int, str, str]]] = {}
        todo = list(glyphs)
        while todo:
            glyph = todo.pop()
            entry = mmah.get(glyph)
            if not entry:
                continue
            parts = extract_components(glyph, entry)
            components[glyph] = parts
            for _, part, _ in parts:
                if part not in glyphs:
                    glyphs.add(part)
                    todo.append(part)
        print(f"{len(glyphs)} characters after adding components")

        # Step 3: gather per-character data
        char_rows = []
        for glyph in sorted(glyphs):
            cp = ord(glyph)
            u = uni.get(cp, {})
            m = mmah.get(glyph, {})

            #fallback to uni if mmah not available
            pinyin = m.get("pinyin") or u.get("kMandarin", "").split()
            meaning = m.get("definition") or u.get("kDefinition")
            strokes = first_int(u.get("kTotalStrokes"))
            radical = first_int(u.get("kRSUnicode"))
            char_rows.append((cp, glyph, pinyin, meaning, strokes, radical))

        # write to the database
        with conn.cursor() as cur:
            cur.executemany(CHAR_SQL, char_rows)
            conn.commit()
        component_rows = [
            (ord(glyph), position, ord(part), role)
            for glyph, parts in components.items()
            for position, part, role in parts
        ]

        with conn.cursor() as cur:
            cur.executemany(COMPONENT_SQL, component_rows) #write char_comp relations

    # Quality report
    no_radical = sum(1 for r in char_rows if r[5] is None)
    no_pinyin = sum(1 for r in char_rows if not r[2])
    print(f"inserted {len(char_rows)} characters, {len(component_rows)} component links")
    print(f"  without main radical: {no_radical}, without pinyin: {no_pinyin}")


if __name__ == "__main__":
    main()