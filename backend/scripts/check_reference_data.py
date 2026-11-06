"""Fail deployment setup if required dictionary datasets have not been loaded."""
from app.db import get_conn


def main():
    with get_conn() as conn:
        counts = conn.execute("""
            SELECT (SELECT count(*) FROM radicals),
                   (SELECT count(*) FROM characters),
                   (SELECT count(*) FROM character_components),
                   (SELECT count(*) FROM words),
                   (SELECT count(*) FROM word_characters)
        """).fetchone()
    print(dict(zip(("radicals", "characters", "components", "words", "word_characters"), counts)))
    if counts[0] != 214 or any(n == 0 for n in counts[1:]):
        raise SystemExit("Reference data incomplete. Run the dictionary import scripts before opening access.")


if __name__ == "__main__":
    main()
