import unicodedata
import sys
import psycopg

from app.db import get_conn
from scripts.utils import first_int, load_unihan

UPSERT_SQL = """
INSERT INTO radicals (id, glyph, pinyin, meaning_en, stroke_count)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (id) DO UPDATE SET
    glyph = EXCLUDED.glyph,
    pinyin = EXCLUDED.pinyin,
    meaning_en = EXCLUDED.meaning_en,
    stroke_count = EXCLUDED.stroke_count
"""

def build_rows():
    data = load_unihan({"kMandarin", "kTotalStrokes"})
    rows = []

    for code_point in range(0x2F00, 0x2FD6):
        #append info for 214 kangxi radicals (1->214)
        k_index = code_point - 0x2F00 + 1

        k_char = chr(code_point)
        glyph = unicodedata.normalize("NFKC", k_char)

        name = unicodedata.name(k_char) # format: "KANGXI RADICAL WOMAN"
        
        meaning = name.replace("KANGXI RADICAL ", "")

        info = data.get(ord(glyph), {})
        mandarin = info.get("kMandarin", "").split()
        pinyin = mandarin[0] if mandarin else None
        n_strokes = first_int(info.get("kTotalStrokes"))

        rows.append((k_index, glyph, pinyin, meaning, n_strokes))
    
    assert len(rows) == 214
    assert len({r[1] for r in rows}) == 214, "radical glyphs contain duplicates"

    return rows



if __name__ == "__main__":
    rows = build_rows()
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.executemany(UPSERT_SQL, rows)
            conn.commit()  # only if you aren't relying on context autocommit
    except KeyError:
        print("DATABASE_URL is not set (check backend/.env)", file=sys.stderr)
        sys.exit(1)
    except psycopg.Error as e:
        print(f"database error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"upserted {len(rows)} radicals")