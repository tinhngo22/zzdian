import asyncio

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.middleware import RequestSizeLimitMiddleware


def test_content_length_and_actual_body_limits():
    app = FastAPI()
    app.add_middleware(RequestSizeLimitMiddleware, max_bytes=8)

    @app.post("/")
    async def echo(request: Request):
        return {"size": len(await request.body())}

    with TestClient(app) as client:
        assert client.post("/", content=b"12345678").json() == {"size": 8}
        assert client.post("/", content=b"123456789").status_code == 413
        assert client.post("/", content=b"123456789", headers={"Content-Length": "1"}).status_code == 413
        assert client.post("/", content=b"", headers={"Content-Length": "bad"}).status_code == 400


def test_streaming_body_is_bounded_without_content_length():
    called = False

    async def downstream(scope, receive, send):
        nonlocal called
        called = True

    chunks = iter([
        {"type": "http.request", "body": b"12345", "more_body": True},
        {"type": "http.request", "body": b"6789", "more_body": False},
    ])
    messages = []

    async def receive():
        return next(chunks)

    async def send(message):
        messages.append(message)

    asyncio.run(RequestSizeLimitMiddleware(downstream, max_bytes=8)(
        {"type": "http", "headers": []}, receive, send,
    ))
    assert not called
    assert messages[0]["status"] == 413
