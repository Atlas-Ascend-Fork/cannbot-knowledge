"""Unit tests for the GitCode login side channel."""
import asyncio
import os
import tempfile
import unittest
import urllib.parse
from pathlib import Path

import server
import state_store


def _form(fields: dict) -> bytes:
    return urllib.parse.urlencode(fields).encode()


class GitCodeLoginTests(unittest.TestCase):
    """/oauth/gitcode/login 302, /oauth/gitcode/callback exchange, fallbacks."""

    def _app(self) -> object:
        async def stub_inner(scope, receive, send) -> None:
            raise AssertionError("side-channel endpoints must not reach the MCP app")

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
        self, app: object, path: str, method: str = "GET", statuses: tuple = (200, 302)
    ) -> tuple[int, dict, bytes]:
        async def receive() -> dict:
            return {"type": "http.request", "body": b"", "more_body": False}

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
        asyncio.run(app(scope, receive, send))
        start = sent[0] if sent and sent[0]["type"] == "http.response.start" else {}
        status = start.get("status")
        headers = {
            k.decode("latin-1").lower(): v.decode("latin-1")
            for k, v in start.get("headers", [])
        }
        payload = b"".join(
            m.get("body", b"") for m in sent if m["type"] == "http.response.body"
        )
        assert status in statuses, (status, payload[:200])
        return status, headers, payload

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
        # Fresh device code for every test.
        status, _headers, payload = self._request(
            self.app, "/oauth/device/code", method="POST", statuses=(200,)
        )
        import json as _json

        self.device = _json.loads(payload)

    def tearDown(self) -> None:
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self._tmp.cleanup()

    def test_login_redirects_to_gitcode_with_pkce(self) -> None:
        status, headers, _ = self._request(
            self.app,
            f"/oauth/gitcode/login?state={self.device['user_code']}",
        )
        self.assertEqual(302, status)
        location = headers["location"]
        self.assertTrue(location.startswith("https://gitcode.com/oauth/authorize?"))
        params = dict(urllib.parse.parse_qsl(location.split("?", 1)[1]))
        self.assertEqual("code", params["response_type"])
        self.assertEqual("cid_test", params["client_id"])
        self.assertEqual("S256", params["code_challenge_method"])
        self.assertEqual(self.device["user_code"], params["state"])
        self.assertIn("/oauth/gitcode/callback", params["redirect_uri"])
        self.assertEqual(43, len(params["code_challenge"]))

    def test_login_without_client_id_shows_fallback_note(self) -> None:
        os.environ.pop(server.OAUTH_CLIENT_ID_ENV, None)
        _status, _headers, payload = self._request(
            self.app,
            f"/oauth/gitcode/login?state={self.device['user_code']}",
            statuses=(200,),
        )
        self.assertIn("未配置 GitCode 登录", payload.decode())

    def test_login_with_unknown_state_rejected(self) -> None:
        _status, _headers, payload = self._request(
            self.app, "/oauth/gitcode/login?state=ZZZZ-ZZZZ", statuses=(200,)
        )
        self.assertIn("重新发起", payload.decode())

    def test_callback_exchanges_code_for_username(self) -> None:
        # Begin a login (stores the PKCE verifier), then mock the exchange.
        self._request(self.app, f"/oauth/gitcode/login?state={self.device['user_code']}")
        captured: dict = {}

        class _TokenResponse:
            status_code = 200

            def json(self) -> dict:
                return {"access_token": "gc-access"}

        class _UserResponse:
            status_code = 200

            def json(self) -> dict:
                return {"login": "demo-user"}

        class _Client:
            async def __aenter__(self) -> "_Client":
                return self

            async def __aexit__(self, *_args: object) -> None:
                return None

            async def post(self, url, data=None, headers=None):
                captured["token_form"] = data
                return _TokenResponse()

            async def get(self, url, headers=None):
                captured["user_url"] = url
                return _UserResponse()

        def fake_client() -> _Client:
            return _Client()

        original = server.httpx.AsyncClient
        server.httpx.AsyncClient = fake_client  # type: ignore[assignment]
        try:
            status, headers, _ = self._request(
                self.app,
                "/oauth/gitcode/callback?code=gc-code&state="
                + self.device["user_code"],
            )
        finally:
            server.httpx.AsyncClient = original
        self.assertEqual(302, status)
        location = headers["location"]
        # The verified username NEVER travels in the URL — only an
        # unguessable server-side binding token does.
        self.assertNotIn("signed_in=", location)
        self.assertIn("st=", location)
        self.assertIn(self.device["user_code"], location)
        # The exchange used the client credentials and the PKCE verifier.
        self.assertEqual("cid_test", captured["token_form"]["client_id"])
        self.assertEqual("sec_test", captured["token_form"]["client_secret"])
        self.assertEqual("authorization_code", captured["token_form"]["grant_type"])
        self.assertEqual(64, len(captured["token_form"]["code_verifier"]))
        self.assertIn("/api/v5/user", captured["user_url"])

    def test_callback_verifier_is_one_shot(self) -> None:
        self._request(self.app, f"/oauth/gitcode/login?state={self.device['user_code']}")
        # First callback consumes the verifier (exchange fails via real httpx
        # is avoided by mocking failure), second must be rejected outright.
        class _FailClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_a):
                return None

            async def post(self, url, data=None, headers=None):
                class R:
                    status_code = 503

                    def json(self):
                        return {}

                return R()

            async def get(self, url, headers=None):
                raise AssertionError("should not be reached")

        def fake():
            return _FailClient()

        original = server.httpx.AsyncClient
        server.httpx.AsyncClient = fake  # type: ignore[assignment]
        try:
            _s, _h, first = self._request(
                self.app,
                "/oauth/gitcode/callback?code=c&state=" + self.device["user_code"],
                statuses=(200,),
            )
        finally:
            server.httpx.AsyncClient = original
        self.assertIn("GitCode 登录失败", first.decode())
        # Second attempt: verifier already consumed.
        _s, _h, second = self._request(
            self.app,
            "/oauth/gitcode/callback?code=c&state=" + self.device["user_code"],
            statuses=(200,),
        )
        self.assertIn("过期或无效", second.decode())

    def test_callback_error_param_shown(self) -> None:
        _s, _h, payload = self._request(
            self.app, "/oauth/gitcode/callback?error=access_denied", statuses=(200,)
        )
        self.assertIn("access_denied", payload.decode())

    def test_signed_in_flow_reaches_confirm_page(self) -> None:
        # GET /activate with code + a server-side binding token renders the
        # GitCode-bound confirm page carrying the verified username.
        binding = server.VerifiedIdentityBinding(state_store.open_state_store())
        st = binding.create(self.device["user_code"], "demo-user")
        _s, _h, payload = self._request(
            self.app,
            "/activate?code=" + self.device["user_code"] + "&st=" + st,
            statuses=(200,),
        )
        html = payload.decode()
        self.assertIn("demo-user", html)
        self.assertIn("GitCode 账号", html)

    def test_signed_in_query_without_binding_redirects_to_login(self) -> None:
        # A crafted /activate?code=..&signed_in=<name> URL carries no
        # server-side binding: it must bounce to the GitCode login, not
        # render a confirmation for the claimed (unverified) identity.
        _status, headers, _payload = self._request(
            self.app,
            "/activate?code=" + self.device["user_code"] + "&signed_in=demo-user",
            method="GET",
            statuses=(302,),
        )
        location = headers["location"]
        self.assertIn("/oauth/gitcode/login", location)

    def test_activate_page_offers_gitcode_login_when_configured(self) -> None:
        _s, _h, payload = self._request(self.app, "/activate", statuses=(200,))
        self.assertIn("使用 GitCode 账号登录", payload.decode())
        # Without client id the link disappears.
        os.environ.pop(server.OAUTH_CLIENT_ID_ENV, None)
        _s, _h, payload = self._request(self.app, "/activate", statuses=(200,))
        self.assertNotIn("使用 GitCode 账号登录", payload.decode())


if __name__ == "__main__":
    unittest.main()
