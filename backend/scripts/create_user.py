"""Admin tool: create a user account (or reset a password).

Usage (from backend/, with DATABASE_URL set in .env or the environment):

    python -m scripts.create_user alice@example.com            # prompts for password
    python -m scripts.create_user alice@example.com --reset    # change existing user's password
    python -m scripts.create_user alice@example.com --password 'secret-pass'

Prefer the prompt: --password ends up in your shell history.
"""
import argparse
import getpass
import sys

import psycopg
from pydantic import TypeAdapter, EmailStr, ValidationError

from app.db import get_conn
from app.security import hash_password

MIN_LEN, MAX_LEN = 8, 128  # same limits the old register endpoint enforced


def read_password(given: str | None) -> str:
    if given is not None:
        return given
    first = getpass.getpass("Password: ")
    if first != getpass.getpass("Repeat password: "):
        print("passwords do not match", file=sys.stderr)
        sys.exit(1)
    return first


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a user account.")
    parser.add_argument("email")
    parser.add_argument("--password", help="omit to be prompted (recommended)")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="update the password of an existing user instead of creating one",
    )
    args = parser.parse_args()

    try:
        email = str(TypeAdapter(EmailStr).validate_python(args.email)).lower()
    except ValidationError:
        print(f"invalid email: {args.email}", file=sys.stderr)
        sys.exit(1)

    password = read_password(args.password)
    if not MIN_LEN <= len(password) <= MAX_LEN:
        print(f"password must be {MIN_LEN}-{MAX_LEN} characters", file=sys.stderr)
        sys.exit(1)

    password_hash = hash_password(password)

    try:
        with get_conn() as conn:
            if args.reset:
                row = conn.execute(
                    "UPDATE users SET password_hash = %s WHERE lower(email) = %s RETURNING id",
                    (password_hash, email),
                ).fetchone()
                if row is None:
                    print(f"no such user: {email}", file=sys.stderr)
                    sys.exit(1)
                print(f"password updated for {email} ({row[0]})")
            else:
                row = conn.execute(
                    "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
                    (email, password_hash),
                ).fetchone()
                print(f"created {email} ({row[0]})")
            conn.commit()
    except psycopg.errors.UniqueViolation:
        print(f"{email} already exists (use --reset to change the password)", file=sys.stderr)
        sys.exit(1)
    except KeyError:
        print("DATABASE_URL is not set (check backend/.env)", file=sys.stderr)
        sys.exit(1)
    except psycopg.Error as e:
        print(f"database error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
