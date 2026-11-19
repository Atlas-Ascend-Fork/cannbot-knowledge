"""End-to-end activation binding tests.

Covers: the allow action binds the GitCode-signed-in username to the device
code, polling mints a self-issued token for that username, denial yields no
token, and the manual-username fallback still works.
"""
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


class ActivationBindingTests(unittest.TestCase):
    """signed_in flow: confirm → allow → poll → token with the bound name."""

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

    def _request(
        self,
        path: str,
        method: str = "POST",
        body: bytes = b"",
        statuses: tuple = (200, 302, 400),
    ) -> tuple[int, dict, bytes]:
        async def receive() -> dict:
            return {"type": "http.request", "body": body, "more_body": False}

        sent: list[dict] = []

        async def send(message: dict) -> None:
            sent.append(message)

        scope = {
            "type": "http",
            "method": method,
            "path": path.split("?")[0],
            "query_string": path.split("?", 1)[1].encode() if "?" in path else b"",
            "headers": [],
            "client": ("10.8.8.8", 44444),
        }
        asyncio.run(self.app(scope, receive, send))
        start = sent[0] if sent and sent[0]["type"] == "http.response.start" else {}
        headers = {
            k.decode("latin-1").lower(): v.decode("latin-1")
            for k, v in start.get("headers", [])
        }
        payload = b"".join(
            m.get("body", b"") for m in sent if m["type"] == "http.response.body"
        )
        assert start.get("status") in statuses, (start.get("status"), payload[:200])
        return start.get("status"), headers, payload

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        env_keys = (
            server.AUTH_DB_ENV,
            server.AUTH_SECRET_ENV,
            server.OAUTH_CLIENT_ID_ENV,
            server.OAUTH_CLIENT_SECRET_ENV,
        )
        self._saved = {k: os.environ.get(k) for k in env_keys}
        os.environ[server.AUTH_DB_ENV] = str(Path(self._tmp.name) / "auth.db")
        os.environ[server.AUTH_SECRET_ENV] = "test-secret"
        os.environ[server.OAUTH_CLIENT_ID_ENV] = "cid_test"
        os.environ[server.OAUTH_CLIENT_SECRET_ENV] = "sec_test"
        self.app = self._app()
        _s, _h, payload = self._request("/oauth/device/code", statuses=(200,))
        self.device = json.loads(payload)

    def tearDown(self) -> None:
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self._tmp.cleanup()

    def _poll(self, device_code: str) -> dict:
        _s, _h, payload = self._request(
            "/oauth/device/token",
            body=_form(
                {
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device_code,
                }
            ),
        )
        return json.loads(payload)

    def _binding(self, code: str, username: str) -> str:
        """Create a server-side verified-identity binding like the callback."""
        store = state_store.open_state_store()
        return server.VerifiedIdentityBinding(store).create(code, username)

    def test_gitcode_signed_in_allow_mints_bound_token(self) -> None:
        # The GitCode login leg ends with a redirect to /activate?code=..&st=..
        # where st references a SERVER-SIDE binding of the verified username.
        st = self._binding(self.device["user_code"], "demo-user")
        _s, _h, page = self._request(
            "/activate?code=" + self.device["user_code"] + "&st=" + st,
            method="GET",
            statuses=(200,),
        )
        html = page.decode()
        self.assertIn("demo-user", html)
        self.assertIn("GitCode 账号", html)
        self.assertIn("允许访问", html)
        # The confirm POST carries the binding token — a username field, if
        # present, is IGNORED (impersonation via form fields is impossible).
        _s, _h, done = self._request(
            "/activate",
            body=_form(
                {
                    "user_code": self.device["user_code"],
                    "st": st,
                    "username": "attacker-name",
                    "action": "allow",
                }
            ),
            statuses=(200,),
        )
        self.assertIn("授权成功", done.decode())
        result = self._poll(self.device["device_code"])
        authority = server.SelfIssuedTokenAuthority()
        self.assertEqual(
            ("demo-user", "access"), authority.verify(result["access_token"], "access")
        )

    def test_allow_without_binding_rejected_when_gitcode_configured(self) -> None:
        # With a GitCode application configured, allow WITHOUT a valid
        # server-side binding must be refused — no manual username path.
        _s, _h, done = self._request(
            "/activate",
            body=_form(
                {
                    "user_code": self.device["user_code"],
                    "username": "forged-user",
                    "action": "allow",
                }
            ),
            statuses=(200,),
        )
        self.assertIn("GitCode 登录", done.decode())
        result = self._poll(self.device["device_code"])
        self.assertEqual("authorization_pending", result.get("error"))

    def test_forged_or_expired_binding_rejected(self) -> None:
        # A fabricated st (never issued by the server) gets the same refusal.
        _s, _h, page = self._request(
            "/activate?code=" + self.device["user_code"] + "&st=forged-token",
            method="GET",
            statuses=(200,),
        )
        self.assertIn("过期或无效", page.decode())
        _s, _h, done = self._request(
            "/activate",
            body=_form(
                {
                    "user_code": self.device["user_code"],
                    "st": "forged-token",
                    "username": "forged-user",
                    "action": "allow",
                }
            ),
            statuses=(200,),
        )
        self.assertIn("GitCode 登录", done.decode())
        result = self._poll(self.device["device_code"])
        self.assertEqual("authorization_pending", result.get("error"))

    def test_binding_is_one_shot(self) -> None:
        st = self._binding(self.device["user_code"], "demo-user")
        _s, _h, _done = self._request(
            "/activate",
            body=_form(
                {"user_code": self.device["user_code"], "st": st, "action": "allow"}
            ),
            statuses=(200,),
        )
        # Replaying the same st for a second grant must fail.
        _s, _h, payload = self._request("/oauth/device/code", statuses=(200,))
        second = json.loads(payload)
        _s, _h, done = self._request(
            "/activate",
            body=_form(
                {"user_code": second["user_code"], "st": st, "action": "allow"}
            ),
            statuses=(200,),
        )
        self.assertIn("GitCode 登录", done.decode())

    def test_manual_username_fallback_still_works(self) -> None:
        # No GitCode application configured: enter the code manually, type a
        # username, allow (trusted-network bootstrap mode).
        os.environ.pop(server.OAUTH_CLIENT_ID_ENV, None)
        _s, _h, done = self._request(
            "/activate",
            body=_form(
                {
                    "user_code": self.device["user_code"],
                    "username": "manual-user",
                    "action": "allow",
                }
            ),
            statuses=(200,),
        )
        self.assertIn("授权成功", done.decode())
        result = self._poll(self.device["device_code"])
        authority = server.SelfIssuedTokenAuthority()
        self.assertEqual(
            ("manual-user", "access"),
            authority.verify(result["access_token"], "access"),
        )

    def test_deny_yields_no_token(self) -> None:
        st = self._binding(self.device["user_code"], "demo-user")
        _s, _h, page = self._request(
            "/activate?code=" + self.device["user_code"] + "&st=" + st,
            method="GET",
            statuses=(200,),
        )
        _s, _h, done = self._request(
            "/activate",
            body=_form(
                {
                    "user_code": self.device["user_code"],
                    "st": st,
                    "action": "deny",
                }
            ),
            statuses=(200,),
        )
        self.assertIn("已拒绝", done.decode())
        result = self._poll(self.device["device_code"])
        self.assertEqual("access_denied", result.get("error"))

    def test_reauthorize_after_deny_with_new_session(self) -> None:
        self.test_deny_yields_no_token()  # deny the first session
        # A fresh device authorization succeeds afterwards (manual mode:
        # no GitCode app configured).
        os.environ.pop(server.OAUTH_CLIENT_ID_ENV, None)
        _s, _h, payload = self._request("/oauth/device/code", statuses=(200,))
        second = json.loads(payload)
        _s, _h, _done = self._request(
            "/activate",
            body=_form(
                {
                    "user_code": second["user_code"],
                    "username": "retry-user",
                    "action": "allow",
                }
            ),
            statuses=(200,),
        )
        result = self._poll(second["device_code"])
        self.assertIn("access_token", result)


if __name__ == "__main__":
    unittest.main()
