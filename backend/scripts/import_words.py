import re

from psycopg.types.json import Jsonb

from app.db import get_conn
from scripts.utils import CEDICT_FILE
from scripts.utils import numbered_to_marked, numbered_to_plain

import sys
import psycopg
LINE_RE = re.compile(r"^(\S+) (\S+) \[(.+?)\] /(.+)/\s*$")

INSERT_SQL = """
INSERT INTO words
    (simplified, traditional, pinyin, pinyin_numbered, pinyin_plain, definitions)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT ON CONSTRAINT uq_word_entry DO UPDATE SET
    pinyin = EXCLUDED.pinyin,
    pinyin_plain = EXCLUDED.pinyin_plain,
    definitions = EXCLUDED.definitions
"""


def parse_cedict(path):
    entries = []
    bad_lines = []
    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            if line.startswith("#") or not line.strip():
                continue
            m = LINE_RE.match(line)
            if not m:
                bad_lines.append((line_number, line.strip()))
                continue

            traditional, simplified, pinyin, defs = m.groups()
            definitions = [d for d in defs.split("/") if d]
            entries.append(
                (
                    simplified,
                    traditional,
                    numbered_to_marked(pinyin),
                    pinyin,
                    numbered_to_plain(pinyin),
                    Jsonb(definitions),   
                )
            )
    return entries, bad_lines


def main():
    entries, bad_lines = parse_cedict(CEDICT_FILE)
    print(f"parsed {len(entries)} entries; {len(bad_lines)} lines did not match")
    for line_number, text in bad_lines[:10]:
        print(f"  line {line_number}: {text}")

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.executemany(INSERT_SQL, entries)
            conn.commit()  # only if you aren't relying on context autocommit
            (count,) = conn.execute("SELECT count(*) FROM words").fetchone()
    except KeyError:
        print("DATABASE_URL is not set (check backend/.env)", file=sys.stderr)
        sys.exit(1)
    except psycopg.Error as e:
        print(f"database error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"words in database: {count} ({len(entries) - count} duplicates skipped)")


if __name__ == "__main__":
    main()