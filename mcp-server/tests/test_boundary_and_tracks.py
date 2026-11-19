"""Boundary and three-track verification tests."""
import asyncio
import json
import os
import tempfile
import unittest
import urllib.parse
from pathlib import Path

import server
import state_store


def _form(fields: dict) -> bytes:
    return urllib.parse.urlencode(fields).encode()


class ThreeTrackAuthTests(unittest.TestCase):
    """static → GitCode → self-issued ordering on the /mcp leg."""

    def _build_app(self, tokens: str, verifier: object) -> object:
        async def stub_inner(scope, receive, send) -> None:
            body = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {"protocolVersion": "2025-06-18", "capabilities": {}},
            }
            payload = json.dumps(body).encode()
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(payload)).encode()),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": payload})

        class StubMcpServer:
            def streamable_http_app(self, **_kwargs: object) -> object:
                return stub_inner

        return server.build_http_app(
            StubMcpServer(),
            server.TokenList.parse(tokens),
            server.SlidingWindowRateLimiter(state_store.open_state_store()),
            server.IpCooldown(state_store.open_state_store()),
            0,
            "127.0.0.1",
            verifier=verifier,
        )

    def _request(self, app: object, token: str | None) -> int:
        async def receive() -> dict:
            return {
                "type": "http.request",
                "body": json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2025-06-18",
                            "capabilities": {},
                            "clientInfo": {"name": "t", "version": "1"},
                        },
                    }
                ).encode(),
                "more_body": False,
            }

        sent: list[dict] = []

        async def send(message: dict) -> None:
            sent.append(message)

        headers = []
        if token is not None:
            headers.append(
                (b"authorization", f"Bearer {token}".encode())
            )
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/mcp",
            "headers": headers,
            "client": ("10.7.7.7", 44444),
        }
        asyncio.run(app(scope, receive, send))
        return sent[0]["status"] if sent else -1

    class _NoVerify:
        async def verify_token(self, token: str) -> None:
            return None

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        env_keys = (server.AUTH_DB_ENV, server.AUTH_SECRET_ENV)
        self._saved = {k: os.environ.get(k) for k in env_keys}
        os.environ[server.AUTH_DB_ENV] = str(Path(self._tmp.name) / "auth.db")
        os.environ[server.AUTH_SECRET_ENV] = "test-secret"
        self.authority = server.SelfIssuedTokenAuthority()

    def tearDown(self) -> None:
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self._tmp.cleanup()

    def test_static_track_still_first(self) -> None:
        app = self._build_app("cbk_static:ready", self._NoVerify())
        self.assertEqual(200, self._request(app, "cbk_static"))

    def test_self_issued_track_accepts_device_token(self) -> None:
        app = self._build_app("cbk_static:ready", self._NoVerify())
        token, _ = self.authority.sign("device-user", "access")
        self.assertEqual(200, self._request(app, token))

    def test_self_issued_refresh_token_rejected_on_mcp_leg(self) -> None:
        app = self._build_app("cbk_static:ready", self._NoVerify())
        token, _ = self.authority.sign("device-user", "refresh")
        self.assertEqual(401, self._request(app, token))

    def test_garbage_token_rejected(self) -> None:
        app = self._build_app("cbk_static:ready", self._NoVerify())
        self.assertEqual(401, self._request(app, "garbage-token"))
        self.assertEqual(401, self._request(app, None))

    def test_expired_self_issued_rejected(self) -> None:
        os.environ[server.ACCESS_TTL_ENV] = "-5"
        try:
            expired_authority = server.SelfIssuedTokenAuthority()
            token, _ = expired_authority.sign("late-user", "access")
        finally:
            os.environ.pop(server.ACCESS_TTL_ENV, None)
        app = self._build_app("cbk_static:ready", self._NoVerify())
        self.assertEqual(401, self._request(app, token))


class SlowDownCadenceTests(unittest.TestCase):
    """Polling faster than the advertised interval gets slow_down."""

    def _app(self) -> object:
        async def stub_inner(scope, receive, send) -> None:
            raise AssertionError("must not reach the MCP app")

        class StubMcpServer:
            def streamable_http_app(self, **_kwargs: object) -> object:
                return stub_inner

        return server.build_http_app(
            StubMcpServer(),
            server.TokenList.parse("cbk_ready:ready"),
            server.SlidingWindowRateLimiter(state_store.open_state_store()),
            server.IpCooldown(state_store.open_state_store()),
            0,
            "127.0.0.1",
        )

    def _poll(self, device_code: str) -> tuple[int, dict]:
        async def receive() -> dict:
            return {
                "type": "http.request",
                "body": _form(
                    {
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                        "device_code": device_code,
                    }
                ),
                "more_body": False,
            }

        sent: list[dict] = []

        async def send(message: dict) -> None:
            sent.append(message)

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/oauth/device/token",
            "headers": [],
            "client": ("10.9.9.9", 44444),
        }
        asyncio.run(self.app(scope, receive, send))
        status = sent[0]["status"]
        payload = b"".join(
            m.get("body", b"") for m in sent if m["type"] == "http.response.body"
        )
        return status, json.loads(payload)

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        env_keys = (server.AUTH_DB_ENV, server.AUTH_SECRET_ENV)
        self._saved = {k: os.environ.get(k) for k in env_keys}
        os.environ[server.AUTH_DB_ENV] = str(Path(self._tmp.name) / "auth.db")
        os.environ[server.AUTH_SECRET_ENV] = "test-secret"
        self.app = self._app()
        # Fresh device.
        async def receive() -> dict:
            return {"type": "http.request", "body": b"", "more_body": False}

        sent: list[dict] = []

        async def send(message: dict) -> None:
            sent.append(message)

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/oauth/device/code",
            "headers": [],
            "client": ("10.9.9.9", 44444),
        }
        asyncio.run(self.app(scope, receive, send))
        payload = b"".join(
            m.get("body", b"") for m in sent if m["type"] == "http.response.body"
        )
        self.device = json.loads(payload)

    def tearDown(self) -> None:
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self._tmp.cleanup()

    def test_rapid_polls_hit_slow_down(self) -> None:
        seen_pending = False
        seen_slow_down = False
        for _ in range(35):
            status, body = self._poll(self.device["device_code"])
            if body.get("error") == "authorization_pending":
                seen_pending = True
            if status == 429 and body.get("error") == "slow_down":
                seen_slow_down = True
                break
        self.assertTrue(seen_pending, "first poll should be authorization_pending")
        self.assertTrue(seen_slow_down, "hammering the poll endpoint must trip slow_down")


if __name__ == "__main__":
    unittest.main()
