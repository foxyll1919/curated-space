from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import request_id_context


class RequestSecurityMiddleware:
    """Bound request bodies, attach a request id and add browser security headers."""

    def __init__(self, app: ASGIApp, *, max_body_bytes: int) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        request_id = headers.get(b"x-request-id", b"").decode("ascii", errors="ignore")
        if (
            not request_id
            or len(request_id) > 128
            or not all(char.isalnum() or char in "-_." for char in request_id)
        ):
            request_id = str(uuid4())
        state = scope.setdefault("state", {})
        state["request_id"] = request_id
        token = request_id_context.set(request_id)

        async def secured_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers", []))
                existing = {name.lower() for name, _value in response_headers}
                defaults = [
                    (b"x-request-id", request_id.encode("ascii")),
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"no-referrer"),
                ]
                response_headers.extend(
                    (name, value) for name, value in defaults if name not in existing
                )
                message["headers"] = response_headers
            await send(message)

        content_length = headers.get(b"content-length")
        try:
            if content_length:
                try:
                    too_large = int(content_length) > self.max_body_bytes
                except ValueError:
                    too_large = True
                if too_large:
                    await self._too_large(secured_send, request_id)
                    return

            chunks: list[bytes] = []
            body_size = 0
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                chunk = message.get("body", b"")
                body_size += len(chunk)
                if body_size > self.max_body_bytes:
                    await self._too_large(secured_send, request_id)
                    return
                chunks.append(chunk)
                if not message.get("more_body", False):
                    break

            sent = False

            async def replay_body() -> Message:
                nonlocal sent
                if not sent:
                    sent = True
                    return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
                return await receive()

            await self.app(scope, replay_body, secured_send)
        finally:
            request_id_context.reset(token)

    @staticmethod
    async def _too_large(send: Callable[[Message], Awaitable[None]], request_id: str) -> None:
        payload = json.dumps(
            {
                "error": {
                    "code": "too_large",
                    "message": "The request body is too large.",
                    "request_id": request_id,
                }
            }
        ).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(payload)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": payload})
