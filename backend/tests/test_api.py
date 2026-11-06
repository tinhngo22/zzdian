"""HTTP regressions in disposable schemas; never migrate the developer's tables."""
import sys
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.db import DATABASE_URL
from app.deps import get_db
from app.main import app
from app.security import hash_password


@pytest.fixture
def api():
    engine = create_engine(DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1))
    with engine.connect() as connection:
        transaction = connection.begin()
        schema = "test_" + uuid4().hex
        try:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            config = Config("alembic.ini")
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            raw = connection.connection.driver_connection

            class RollbackConnection:
                def __getattr__(self, name):
                    return getattr(raw, name)

                def commit(self):
                    pass

                def __enter__(self):
                    return self

                def __exit__(self, *_):
                    pass

            db = RollbackConnection()

            def override_db():
                yield db

            app.dependency_overrides[get_db] = override_db
            client = TestClient(app)
            email = f"{uuid4()}@example.com"
            user = raw.execute(
                "INSERT INTO users(email, password_hash) VALUES (%s, %s) RETURNING id",
                (email, hash_password("test-password")),
            ).fetchone()[0]
            result = client.post("/auth/login", json={"email": email, "password": "test-password"})
            assert result.status_code == 200
            headers = {"Authorization": "Bearer " + result.json()["access_token"]}
            yield client, db, user, email, headers, config
            client.close()
        finally:
            app.dependency_overrides.clear()
            transaction.rollback()
    engine.dispose()


def test_auth_and_set_lifecycle(api):
    c, db, user, email, h, _ = api
    assert c.get("/sets").status_code == 401
    assert c.get("/auth/me", headers=h).json()["id"] == str(user)
    assert c.post("/auth/login", json={"email": email, "password": "wrong"}).status_code == 401
    result = c.post("/sets", headers=h, json={"name": " test "})
    assert result.status_code == 201
    sid = result.json()["id"]
    assert result.json()["name"] == "test"
    assert c.patch(f"/sets/{sid}", headers=h, json={"name": "renamed"}).status_code == 200
    word = c.post(f"/sets/{sid}/words", headers=h, json={"simplified": "hello"})
    assert word.status_code == 201
    assert c.get(f"/sets/{sid}/words", headers=h).json()["total"] == 1
    assert c.delete(f"/sets/{sid}/words/{word.json()['id']}", headers=h).status_code == 204
    assert c.delete(f"/sets/{sid}", headers=h).status_code == 204


def test_deleted_account_is_rejected_on_reads_and_writes(api):
    c, db, user, _, h, _ = api
    db.execute("DELETE FROM users WHERE id = %s", (user,))
    assert c.get("/sets", headers=h).status_code == 401
    assert c.post("/sets", headers=h, json={"name": "test"}).status_code == 401


def test_admin_password_reset_revokes_existing_sessions(api, monkeypatch):
    from scripts import create_user

    c, db, _, email, h, _ = api
    monkeypatch.setattr(create_user, "get_conn", lambda: db)
    monkeypatch.setattr(sys, "argv", ["create_user", email, "--reset", "--password", "replacement-pass"])
    create_user.main()
    assert c.get("/sets", headers=h).status_code == 401
    assert c.post("/auth/login", json={"email": email, "password": "test-password"}).status_code == 401
    token = c.post("/auth/login", json={"email": email, "password": "replacement-pass"}).json()["access_token"]
    assert c.get("/sets", headers={"Authorization": "Bearer " + token}).status_code == 200


def test_cross_user_access_and_bulk_atomicity(api):
    from app.security import create_access_token

    c, db, _, _, h, _ = api
    other_id = db.execute("INSERT INTO users(email,password_hash) VALUES (%s,'unused') RETURNING id", (f"{uuid4()}@example.com",)).fetchone()[0]
    other = {"Authorization": "Bearer " + create_access_token(str(other_id))}
    sid = c.post("/sets", headers=h, json={"name": "private"}).json()["id"]
    for method, path, body in [
        ("GET", f"/sets/{sid}/words", None),
        ("PATCH", f"/sets/{sid}", {"name": "hijack"}),
        ("DELETE", f"/sets/{sid}", None),
        ("POST", f"/sets/{sid}/words", {"simplified": "x"}),
        ("POST", f"/sets/{sid}/words/bulk", {"words": [{"simplified": "x"}]}),
    ]:
        assert c.request(method, path, headers=other, json=body).status_code == 404
    assert c.post(f"/sets/{sid}/words/bulk", headers=h, json={"words": [{"simplified": "valid"}, {"simplified": " "}]}).status_code == 422
    assert c.get(f"/sets/{sid}/words", headers=h).json()["total"] == 0
    assert c.post(f"/sets/{sid}/words/bulk", headers=h, json={"words": [{"simplified": "a"}, {"simplified": "b"}]}).status_code == 201
    assert c.get(f"/sets/{sid}/words", headers=h).json()["total"] == 2


@pytest.mark.parametrize("field,length", [("simplified", 101), ("traditional", 101), ("pinyin", 501), ("definitions", 10001)])
def test_word_limits_reject_without_inserting(api, field, length):
    c, _, _, _, h, _ = api
    sid = c.post("/sets", headers=h, json={"name": "limits"}).json()["id"]
    body = {"simplified": "test", field: "x" * length}
    assert c.post(f"/sets/{sid}/words", headers=h, json=body).status_code == 422
    assert c.post(f"/sets/{sid}/words/bulk", headers=h, json={"words": [body]}).status_code == 422
    assert c.get(f"/sets/{sid}/words", headers=h).json()["total"] == 0


def test_password_limit(api):
    c, _, _, email, _, _ = api
    assert c.post("/auth/login", json={"email": email, "password": "x" * 129}).status_code == 422


def test_empty_reference_data_is_rejected(api, monkeypatch):
    from scripts import check_reference_data, import_characters, build_word_characters

    _, db, _, _, _, _ = api
    for script in [check_reference_data, import_characters, build_word_characters]:
        monkeypatch.setattr(script, "get_conn", lambda: db)
    monkeypatch.setattr(import_characters, "load_unihan", lambda _: {})
    monkeypatch.setattr(import_characters, "load_mmah", lambda: {})
    with pytest.raises(SystemExit, match="Reference data incomplete"):
        check_reference_data.main()
    with pytest.raises(SystemExit, match="import_words"):
        import_characters.main()
    with pytest.raises(SystemExit, match="import_characters"):
        build_word_characters.main()


def test_migrations_are_repeatable_and_token_version_can_be_downgraded(api):
    _, db, _, _, _, config = api
    command.upgrade(config, "head")
    command.downgrade(config, "609bb6b11ba5")
    command.upgrade(config, "head")
    assert db.execute("SELECT token_version FROM users").fetchone()[0] == 0
