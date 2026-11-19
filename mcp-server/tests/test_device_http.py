"""ASGI-level tests for the device-code HTTP endpoints."""
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


class DeviceCodeHttpTests(unittest.TestCase):
    """POST /oauth/device/code, POST /oauth/device/token, GET/POST /activate."""

    def _app(self) -> object:
        async def stub_inner(scope, receive, send) -> None:
            raise AssertionError("device endpoints must not reach the MCP app")

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

    def _request(
        self,
        app: object,
        path: str,
        method: str = "POST",
        body: bytes = b"",
        statuses: tuple = (200, 400),
    ) -> tuple[dict | None, bytes]:
        received: dict = {"done": False, "body": b""}

        async def receive() -> dict:
            return {"type": "http.request", "body": body, "more_body": False}

        sent: list[dict] = []

        async def send(message: dict) -> None:
            sent.append(message)

        scope = {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [],
            "client": ("10.8.8.8", 44444),
        }
        asyncio.run(app(scope, receive, send))
        status = sent[0]["status"] if sent else None
        payload = b"".join(
            m.get("body", b"") for m in sent if m["type"] == "http.response.body"
        )
        assert status in statuses, (status, payload[:200])
        try:
            parsed = json.loads(payload)
        except ValueError:
            parsed = None
        return parsed, payload

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        saved_db = os.environ.get(server.AUTH_DB_ENV)
        saved_secret = os.environ.get(server.AUTH_SECRET_ENV)
        os.environ[server.AUTH_DB_ENV] = str(Path(self._tmp.name) / "auth.db")
        os.environ[server.AUTH_SECRET_ENV] = "test-secret"
        self._saved = (saved_db, saved_secret)
        self.app = self._app()

    def tearDown(self) -> None:
        saved_db, saved_secret = self._saved
        if saved_db is None:
            os.environ.pop(server.AUTH_DB_ENV, None)
        else:
            os.environ[server.AUTH_DB_ENV] = saved_db
        if saved_secret is None:
            os.environ.pop(server.AUTH_SECRET_ENV, None)
        else:
            os.environ[server.AUTH_SECRET_ENV] = saved_secret
        self._tmp.cleanup()

    def _new_device(self) -> dict:
        payload, _ = self._request(self.app, "/oauth/device/code")
        assert payload is not None
        return payload

    def test_device_code_shape(self) -> None:
        payload = self._new_device()
        self.assertIn("device_code", payload)
        self.assertIn("user_code", payload)
        self.assertTrue(payload["verification_uri"].endswith("/activate"))
        self.assertEqual(600, payload["expires_in"])
        self.assertEqual(5, payload["interval"])

    def test_full_roundtrip_pending_to_allowed(self) -> None:
        device = self._new_device()
        # pending on first poll
        payload, _ = self._request(
            self.app,
            "/oauth/device/token",
            body=_form(
                {
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device["device_code"],
                }
            ),
        )
        self.assertEqual("authorization_pending", payload["error"])
        # activate: confirm page then allow with a username
        payload, html = self._request(
            self.app,
            "/activate",
            method="POST",
            body=_form({"user_code": device["user_code"]}),
            statuses=(200,),
        )
        self.assertIn(device["user_code"], html.decode())
        payload, html = self._request(
            self.app,
            "/activate",
            method="POST",
            body=_form(
                {
                    "user_code": device["user_code"],
                    "username": "demo-user",
                    "action": "allow",
                }
            ),
            statuses=(200,),
        )
        self.assertIn("demo-user", html.decode())
        # poll now succeeds and the token verifies back to the username
        payload, _ = self._request(
            self.app,
            "/oauth/device/token",
            body=_form(
                {
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device["device_code"],
                }
            ),
        )
        authority = server.SelfIssuedTokenAuthority()
        verified = authority.verify(payload["access_token"], "access")
        self.assertEqual(("demo-user", "access"), verified)
        self.assertGreater(payload["expires_in"], 0)
        # one-shot: polling again after success no longer yields tokens
        payload, _ = self._request(
            self.app,
            "/oauth/device/token",
            body=_form(
                {
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device["device_code"],
                }
            ),
        )
        self.assertEqual("expired_token", payload["error"])

    def test_denied_flow(self) -> None:
        device = self._new_device()
        self._request(
            self.app,
            "/activate",
            method="POST",
            body=_form({"user_code": device["user_code"], "action": "deny"}),
            statuses=(200,),
        )
        payload, _ = self._request(
            self.app,
            "/oauth/device/token",
            body=_form(
                {
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device["device_code"],
                }
            ),
        )
        self.assertEqual("access_denied", payload["error"])

    def test_expired_token_error(self) -> None:
        payload, _ = self._request(
            self.app,
            "/oauth/device/token",
            body=_form(
                {
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": "bogus",
                }
            ),
        )
        self.assertEqual("expired_token", payload["error"])

    def test_unsupported_grant_type(self) -> None:
        payload, _ = self._request(
            self.app,
            "/oauth/device/token",
            body=_form({"grant_type": "password"}),
        )
        self.assertEqual("unsupported_grant_type", payload["error"])

    def test_refresh_grant_rotates_tokens(self) -> None:
        authority = server.SelfIssuedTokenAuthority()
        refresh, _ = authority.sign("rotating-user", "refresh")
        # One-time-use ledger (13b): only a booked id refreshes; book it
        # the way every mint site (device flow / authcode / refresh) does.
        jti = authority.token_jti(refresh)
        assert jti is not None
        store = state_store.open_state_store()
        store.put(f"jti:{jti}", "live", authority.refresh_remaining_s(refresh))
        try:
            payload, _ = self._request(
                self.app,
                "/oauth/device/token",
                body=_form(
                    {"grant_type": "refresh_token", "refresh_token": refresh}
                ),
            )
            self.assertEqual(
                ("rotating-user", "access"),
                authority.verify(payload["access_token"], "access"),
            )
            self.assertEqual(
                ("rotating-user", "refresh"),
                authority.verify(payload["refresh_token"], "refresh"),
            )
            new_refresh = payload["refresh_token"]
            # the OLD refresh is consumed: replaying it gets invalid_grant
            payload, _ = self._request(
                self.app,
                "/oauth/device/token",
                body=_form(
                    {
                        "grant_type": "refresh_token",
                        "refresh_token": refresh,
                    }
                ),
            )
            self.assertEqual("invalid_grant", payload["error"])
            # the NEW refresh was booked by the server: it works
            payload2, _ = self._request(
                self.app,
                "/oauth/device/token",
                body=_form(
                    {
                        "grant_type": "refresh_token",
                        "refresh_token": new_refresh,
                    }
                ),
            )
            self.assertIn("access_token", payload2)
            # invalid refresh is rejected (signature check precedes ledger)
            payload3, _ = self._request(
                self.app,
                "/oauth/device/token",
                body=_form(
                    {
                        "grant_type": "refresh_token",
                        "refresh_token": "junk",
                    }
                ),
            )
            self.assertEqual("invalid_grant", payload3["error"])
        finally:
            store.close()

    def test_activate_rejects_unknown_code(self) -> None:
        _payload, html = self._request(
            self.app,
            "/activate",
            method="POST",
            body=_form({"user_code": "ZZZZ-ZZZZ"}),
            statuses=(200,),
        )
        self.assertIn("重新发起", html.decode())

    def test_activate_get_shows_form(self) -> None:
        _payload, html = self._request(
            self.app, "/activate", method="GET", statuses=(200,)
        )
        self.assertIn("设备授权", html.decode())


if __name__ == "__main__":
    unittest.main()
