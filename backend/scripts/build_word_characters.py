from collections import Counter

from app.db import get_conn

INSERT_SQL = """
INSERT INTO word_characters (word_id, position, character_id)
VALUES (%s, %s, %s)
"""


def main():
    with get_conn() as conn:
        char_ids = {row[0] for row in conn.execute("SELECT id FROM characters")}

        rows = []
        skipped = Counter()
        for word_id, simplified in conn.execute("SELECT id, simplified FROM words"):
            for position, ch in enumerate(simplified):
                if ord(ch) in char_ids:
                    rows.append((word_id, position, ord(ch)))
                else:
                    skipped[ch] += 1   # Latin letters, digits, punctuation, etc.

        with conn.cursor() as cur:
            cur.executemany(INSERT_SQL, rows)
            conn.commit()

    print(f"inserted {len(rows)} word-character links")
    print(f"skipped {sum(skipped.values())} non-character symbols; most common: "
          f"{skipped.most_common(10)}")


if __name__ == "__main__":
    main()