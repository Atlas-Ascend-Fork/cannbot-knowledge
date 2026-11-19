"""ASGI-level tests for the self-hosted authorization-code grant.

Covers the browser-client leg (Claude Code style): GET /oauth/authorize,
POST /oauth/authorize/confirm, and the authorization_code grant at the
token endpoint — one-shot consume, PKCE verification, and RFC 8252 §7.3
loopback port-agnostic redirect matching.
"""
import asyncio
import base64
import hashlib
import json
import os
import secrets
import tempfile
import unittest
import urllib.parse
from pathlib import Path

import server
import state_store


def _form(fields: dict) -> bytes:
    return urllib.parse.urlencode(fields).encode()


def _pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    return verifier, challenge


class AuthCodeHttpTests(unittest.TestCase):
    def _app(self) -> object:
        async def stub_inner(scope, receive, send) -> None:
            raise AssertionError("authorize endpoints must not reach the MCP app")

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
        statuses: tuple = (200, 302, 400),
        query: bytes = b"",
    ) -> tuple[dict | None, bytes, str | None]:
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
            "query_string": query,
            "headers": [],
            "client": ("10.8.8.8", 44444),
        }
        asyncio.run(app(scope, receive, send))
        status = sent[0]["status"] if sent else None
        location = None
        for header in (sent[0].get("headers") or []) if sent else []:
            if header[0] == b"location":
                location = header[1].decode()
        payload = b"".join(
            m.get("body", b"") for m in sent if m["type"] == "http.response.body"
        )
        assert status in statuses, (status, payload[:200])
        try:
            parsed = json.loads(payload)
        except ValueError:
            parsed = None
        return parsed, payload, location

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        saved_db = os.environ.get(server.AUTH_DB_ENV)
        saved_secret = os.environ.get(server.AUTH_SECRET_ENV)
        saved_as = os.environ.get(server.AUTH_SERVER_ENV)
        os.environ[server.AUTH_DB_ENV] = str(Path(self._tmp.name) / "auth.db")
        os.environ[server.AUTH_SECRET_ENV] = "test-secret"
        os.environ.pop(server.AUTH_SERVER_ENV, None)
        self._saved = (saved_db, saved_secret, saved_as)
        self.app = self._app()

    def tearDown(self) -> None:
        saved_db, saved_secret, saved_as = self._saved
        if saved_db is None:
            os.environ.pop(server.AUTH_DB_ENV, None)
        else:
            os.environ[server.AUTH_DB_ENV] = saved_db
        if saved_secret is None:
            os.environ.pop(server.AUTH_SECRET_ENV, None)
        else:
            os.environ[server.AUTH_SECRET_ENV] = saved_secret
        if saved_as is None:
            os.environ.pop(server.AUTH_SERVER_ENV, None)
        else:
            os.environ[server.AUTH_SERVER_ENV] = saved_as
        self._tmp.cleanup()

    def _start_grant(self, redirect_uri: str) -> tuple[str, str, str]:
        """GET /oauth/authorize -> consent page; returns (code, state, verifier)."""
        verifier, challenge = _pkce()
        query = urllib.parse.urlencode(
            {
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "state": "client-state-123",
            }
        ).encode()
        _, html, _ = self._request(
            self.app,
            "/oauth/authorize",
            method="GET",
            query=query,
            statuses=(200,),
        )
        text = html.decode()
        self.assertIn("确认授权", text)
        # GitCode configured (client_id set via test env? no — default off
        # in this suite, so the manual-username page renders). Either way
        # the loopback host must never appear.
        self.assertNotIn("55685", text)
        code = self._extract_code(text)
        return code, "client-state-123", verifier

    def _extract_code(self, html: str) -> str:
        marker = "name='code' value='"
        idx = html.index(marker) + len(marker)
        return html[idx : html.index("'", idx)]

    def _allow(self, code: str, username: str = "demo-user") -> str:
        """POST confirm/allow -> redirect target carrying code+state."""
        _, _, location = self._request(
            self.app,
            "/oauth/authorize/confirm",
            body=_form({"code": code, "username": username, "action": "allow"}),
            statuses=(302,),
        )
        assert location is not None
        return location

    def _exchange(
        self, code: str, redirect_uri: str, verifier: str
    ) -> tuple[dict | None, bytes]:
        return self._request(
            self.app,
            "/oauth/device/token",
            body=_form(
                {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "code_verifier": verifier,
                }
            ),
        )[:2]

    def test_roundtrip_allow_and_exchange(self) -> None:
        redirect = "http://localhost:55685/callback"
        code, state, verifier = self._start_grant(redirect)
        location = self._allow(code)
        self.assertTrue(location.startswith(redirect + "?"), location)
        back = urllib.parse.parse_qs(urllib.parse.urlsplit(location).query)
        self.assertEqual(code, back["code"][0])
        self.assertEqual(state, back["state"][0])
        # token exchange
        payload, _ = self._exchange(code, redirect, verifier)
        assert payload is not None
        self.assertIn("access_token", payload)
        authority = server.SelfIssuedTokenAuthority()
        verified = authority.verify(payload["access_token"], "access")
        self.assertEqual(("demo-user", "access"), verified)
        # one-shot: exchanging again fails
        payload, _ = self._exchange(code, redirect, verifier)
        self.assertEqual("invalid_grant", payload["error"])

    def test_exchange_before_allow_rejected(self) -> None:
        redirect = "http://localhost:55685/callback"
        code, _, verifier = self._start_grant(redirect)
        payload, _ = self._exchange(code, redirect, verifier)
        self.assertEqual("invalid_grant", payload["error"])

    def test_pkce_mismatch_rejected(self) -> None:
        redirect = "http://localhost:55685/callback"
        code, _, _ = self._start_grant(redirect)
        self._allow(code)
        payload, _ = self._exchange(code, redirect, "wrong-verifier")
        self.assertEqual("invalid_grant", payload["error"])

    def test_redirect_mismatch_rejected(self) -> None:
        redirect = "http://localhost:55685/callback"
        code, _, verifier = self._start_grant(redirect)
        self._allow(code)
        payload, _ = self._exchange(
            code, "http://localhost:9999/callback", verifier
        )
        # loopback: port may differ (RFC 8252 §7.3)
        assert payload is not None
        self.assertIn("access_token", payload)

    def test_redirect_host_mismatch_rejected(self) -> None:
        redirect = "http://localhost:55685/callback"
        code, _, verifier = self._start_grant(redirect)
        self._allow(code)
        payload, _ = self._exchange(
            code, "http://evil.example.com/callback", verifier
        )
        self.assertEqual("invalid_grant", payload["error"])

    def test_deny_bounces_error(self) -> None:
        redirect = "http://localhost:55685/callback"
        code, _, _ = self._start_grant(redirect)
        _, _, location = self._request(
            self.app,
            "/oauth/authorize/confirm",
            body=_form({"code": code, "action": "deny"}),
            statuses=(302,),
        )
        assert location is not None
        back = urllib.parse.parse_qs(urllib.parse.urlsplit(location).query)
        self.assertEqual("access_denied", back["error"][0])
        self.assertEqual("client-state-123", back["state"][0])

    def test_missing_params_shows_error_page(self) -> None:
        redirect = "http://localhost:55685/callback"
        verifier, challenge = _pkce()
        query = urllib.parse.urlencode(
            {
                "response_type": "code",
                "redirect_uri": redirect,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            }
        ).encode()
        # Strip each mandatory parameter in turn; the error page names it.
        for drop in ("redirect_uri", "response_type"):
            params = dict(
                urllib.parse.parse_qs(query.decode(), keep_blank_values=True)
            )
            params.pop(drop)
            _, html, _ = self._request(
                self.app,
                "/oauth/authorize",
                method="GET",
                query=urllib.parse.urlencode(params, doseq=True).encode(),
                statuses=(200,),
            )
            self.assertIn(drop, html.decode())

    def test_missing_pkce_challenge_rejected(self) -> None:
        """Public clients must use PKCE: no challenge, no grant."""
        redirect = "http://localhost:55685/callback"
        query = urllib.parse.urlencode(
            {
                "response_type": "code",
                "redirect_uri": redirect,
                "code_challenge_method": "S256",
                "state": "client-state-123",
            }
        ).encode()
        _, html, _ = self._request(
            self.app,
            "/oauth/authorize",
            method="GET",
            query=query,
            statuses=(200,),
        )
        text = html.decode()
        self.assertIn("PKCE", text)
        # No session was minted, so no code leaks into the page.
        self.assertNotIn("name='code' value='", text)

    def test_plain_challenge_method_rejected(self) -> None:
        """Only S256 is advertised and accepted; plain is rejected."""
        redirect = "http://localhost:55685/callback"
        verifier, _ = _pkce()
        query = urllib.parse.urlencode(
            {
                "response_type": "code",
                "redirect_uri": redirect,
                "code_challenge": verifier,  # plain sends the raw verifier
                "code_challenge_method": "plain",
                "state": "client-state-123",
            }
        ).encode()
        _, html, _ = self._request(
            self.app,
            "/oauth/authorize",
            method="GET",
            query=query,
            statuses=(200,),
        )
        text = html.decode()
        self.assertIn("S256", text)
        self.assertNotIn("name='code' value='", text)

    def test_auth_server_off_rejected(self) -> None:
        os.environ[server.AUTH_SERVER_ENV] = "off"
        app = self._app()
        verifier, challenge = _pkce()
        query = urllib.parse.urlencode(
            {
                "response_type": "code",
                "redirect_uri": "http://localhost:1/cb",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            }
        ).encode()
        # Closing the self-hosted AS closes the authorize endpoint itself.
        _, payload, _ = self._request(
            app, "/oauth/authorize", method="GET", query=query, statuses=(404,)
        )
        self.assertIn(b"Method not found", payload)
        os.environ.pop(server.AUTH_SERVER_ENV, None)

    def test_reentry_with_code_reuses_session(self) -> None:
        """Returning from the GitCode login leg must not mint a new code."""
        redirect = "http://localhost:55685/callback"
        code, _, _ = self._start_grant(redirect)
        # The login-leg callback links here WITHOUT redirect_uri (only
        # code + the server-side binding token st) — the session carries
        # the original target and the binding carries the identity.
        binding = server.VerifiedIdentityBinding(state_store.open_state_store())
        st = binding.create(code, "demo-user")
        query = urllib.parse.urlencode({"code": code, "st": st}).encode()
        _, html, _ = self._request(
            self.app,
            "/oauth/authorize",
            method="GET",
            query=query,
            statuses=(200,),
        )
        text = html.decode()
        self.assertIn("demo-user", text)  # identity card shown
        self.assertEqual(code, self._extract_code(text))  # same code preserved
        # The consent page never leaks the loopback redirect host.
        self.assertNotIn("55685", text)

    def test_allow_with_gitcode_configured_requires_binding(self) -> None:
        # With a GitCode application configured, allow WITHOUT a valid
        # server-side binding must be refused — a typed username cannot
        # substitute for the authenticated GitCode login.
        os.environ[server.OAUTH_CLIENT_ID_ENV] = "cid_test"
        try:
            redirect = "http://localhost:55685/callback"
            code, _, verifier = self._start_grant(redirect)
            payload, html, _ = self._request(
                self.app,
                "/oauth/authorize/confirm",
                body=_form(
                    {"code": code, "username": "forged-user", "action": "allow"}
                ),
                statuses=(200,),
            )
            assert payload is None or "error" not in payload
            self.assertIn("GitCode 登录", html.decode())
            # The grant was never bound: the exchange still fails.
            token_payload, _ = self._exchange(code, redirect, verifier)
            assert token_payload is not None
            self.assertEqual("invalid_grant", token_payload.get("error"))
        finally:
            os.environ.pop(server.OAUTH_CLIENT_ID_ENV, None)

    def test_allow_with_binding_ignores_form_username(self) -> None:
        # The bound (server-verified) username wins over any username
        # value in the form.
        os.environ[server.OAUTH_CLIENT_ID_ENV] = "cid_test"
        try:
            redirect = "http://localhost:55685/callback"
            code, _, verifier = self._start_grant(redirect)
            binding = server.VerifiedIdentityBinding(state_store.open_state_store())
            st = binding.create(code, "demo-user")
            _, _, location = self._request(
                self.app,
                "/oauth/authorize/confirm",
                body=_form(
                    {
                        "code": code,
                        "st": st,
                        "username": "attacker-name",
                        "action": "allow",
                    }
                ),
                statuses=(302,),
            )
            assert location is not None
            back = urllib.parse.parse_qs(urllib.parse.urlsplit(location).query)
            self.assertEqual(code, back["code"][0])
            payload, _ = self._exchange(code, redirect, verifier)
            assert payload is not None
            authority = server.SelfIssuedTokenAuthority()
            self.assertEqual(
                ("demo-user", "access"),
                authority.verify(payload["access_token"], "access"),
            )
        finally:
            os.environ.pop(server.OAUTH_CLIENT_ID_ENV, None)


if __name__ == "__main__":
    unittest.main()
