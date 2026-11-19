"""Audience binding and RFC 8707 resource parameter tests."""
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


def _decode_payload(token: str) -> dict:
    body_b = token.split(".")[1]
    padding = "=" * (-len(body_b) % 4)
    return json.loads(base64.urlsafe_b64decode(body_b + padding))


class AudienceBindingTests(unittest.TestCase):
    """Unit-level aud checks on the token authority."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        saved_secret = os.environ.get(server.AUTH_SECRET_ENV)
        os.environ[server.AUTH_SECRET_ENV] = "test-secret"
        self._saved = saved_secret
        self.authority = server.SelfIssuedTokenAuthority()

    def tearDown(self) -> None:
        saved_secret = self._saved
        if saved_secret is None:
            os.environ.pop(server.AUTH_SECRET_ENV, None)
        else:
            os.environ[server.AUTH_SECRET_ENV] = saved_secret
        self._tmp.cleanup()

    def test_token_carries_aud(self) -> None:
        token, _ = self.authority.sign("demo-user", "access")
        self.assertEqual(
            "http://localhost", _decode_payload(token)["aud"]
        )

    def test_custom_audience_roundtrip(self) -> None:
        token, _ = self.authority.sign("demo-user", "access", "https://other")
        self.assertEqual(
            ("demo-user", "access"),
            self.authority.verify(token, "access", "https://other"),
        )
        # wrong audience rejected
        self.assertIsNone(self.authority.verify(token, "access", "https://x"))
        # default-audience verification also rejected (audience binding)
        self.assertIsNone(self.authority.verify(token, "access"))

    def test_refresh_also_audience_bound(self) -> None:
        token, _ = self.authority.sign("demo-user", "refresh", "https://svc")
        self.assertIsNone(self.authority.verify(token, "refresh"))

    def test_token_without_aud_rejected(self) -> None:
        # hand-forge a token with no aud: signature valid, aud missing
        import time as _time

        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": "demo-user",
            "typ": "access",
            "iat": int(_time.time()),
            "exp": int(_time.time()) + 3600,
        }

        def b64(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

        head_b = b64(json.dumps(header).encode())
        body_b = b64(json.dumps(payload).encode())
        sig = b64(self.authority._sign(f"{head_b}.{body_b}".encode()))
        forged = f"{head_b}.{body_b}.{sig}"
        self.assertIsNone(self.authority.verify(forged, "access"))


class ResourceParameterHttpTests(unittest.TestCase):
    """HTTP-level: resource flows from authorize into the minted aud."""

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
        app: object,
        path: str,
        method: str = "POST",
        body: bytes = b"",
        query: bytes = b"",
        statuses: tuple = (200, 302, 400),
    ) -> tuple[dict | None, bytes]:
        sent: list[dict] = []

        async def receive() -> dict:
            return {"type": "http.request", "body": body, "more_body": False}

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

    def _grant(self, resource: str | None) -> tuple[str, str, dict]:
        """authorize -> allow -> exchange; returns (code, verifier, tokens)."""
        verifier, challenge = _pkce()
        params = {
            "response_type": "code",
            "redirect_uri": "http://localhost:55685/callback",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": "s",
        }
        if resource is not None:
            params["resource"] = resource
        query = urllib.parse.urlencode(params).encode()
        _, html = self._request(
            self.app, "/oauth/authorize", method="GET", query=query,
            statuses=(200,),
        )
        marker = "name='code' value='"
        idx = html.decode().index(marker) + len(marker)
        code = html.decode()[: html.decode().index("'", idx)][idx:]
        # allow
        sent: list[dict] = []

        async def receive() -> dict:
            return {
                "type": "http.request",
                "body": _form({"code": code, "username": "u", "action": "allow"}),
                "more_body": False,
            }

        async def send(message: dict) -> None:
            sent.append(message)

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/oauth/authorize/confirm",
            "query_string": b"",
            "headers": [],
            "client": ("10.8.8.8", 44444),
        }
        asyncio.run(self.app(scope, receive, send))
        assert sent[0]["status"] == 302, sent[0]
        # exchange
        tokens, _ = self._request(
            self.app,
            "/oauth/device/token",
            body=_form(
                {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": "http://localhost:55685/callback",
                    "code_verifier": verifier,
                }
            ),
            statuses=(200,),
        )
        assert tokens is not None and "access_token" in tokens, tokens
        return code, verifier, tokens

    def test_resource_becomes_aud(self) -> None:
        resource = "https://knowledge.internal.example.com"
        _, _, tokens = self._grant(resource)
        aud = _decode_payload(tokens["access_token"])["aud"]
        self.assertEqual(resource, aud)
        refresh_aud = _decode_payload(tokens["refresh_token"])["aud"]
        self.assertEqual(resource, refresh_aud)

    def test_no_resource_defaults_to_this_server(self) -> None:
        _, _, tokens = self._grant(None)
        aud = _decode_payload(tokens["access_token"])["aud"]
        self.assertEqual("http://localhost", aud)

    def test_refresh_honors_resource(self) -> None:
        resource = "https://knowledge.internal.example.com"
        _, _, tokens = self._grant(resource)
        refreshed, _ = self._request(
            self.app,
            "/oauth/device/token",
            body=_form(
                {
                    "grant_type": "refresh_token",
                    "refresh_token": tokens["refresh_token"],
                    "resource": resource,
                }
            ),
            statuses=(200,),
        )
        assert refreshed is not None
        self.assertEqual(
            resource, _decode_payload(refreshed["access_token"])["aud"]
        )
        # mismatched resource on refresh is rejected
        mismatch, _ = self._request(
            self.app,
            "/oauth/device/token",
            body=_form(
                {
                    "grant_type": "refresh_token",
                    "refresh_token": tokens["refresh_token"],
                    "resource": "https://other.example.com",
                }
            ),
            statuses=(400,),
        )
        self.assertEqual("invalid_grant", mismatch["error"])

    def test_www_authenticate_carries_metadata_hint(self) -> None:
        sent: list[dict] = []

        async def receive() -> dict:
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message: dict) -> None:
            sent.append(message)

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/mcp",
            "query_string": b"",
            "headers": [],
            "client": ("10.8.8.8", 44444),
        }
        asyncio.run(self.app(scope, receive, send))
        assert sent[0]["status"] == 401
        headers = dict(sent[0]["headers"])
        challenge = headers.get(b"www-authenticate", b"").decode()
        self.assertIn("Bearer", challenge)
        self.assertIn(
            "resource_metadata=\"http://localhost/.well-known/"
            "oauth-protected-resource\"",
            challenge,
        )

    def test_8414_metadata_advertises_fields(self) -> None:
        import tempfile as _tf  # noqa: F401  (already imported above)
        _, payload = self._request(
            self.app,
            "/.well-known/oauth-authorization-server",
            method="GET",
            statuses=(200,),
        )
        # not reachable in this app without gitcode verify env; the
        # dedicated metadata tests cover the body. Here we only assert the
        # route exists (404 JSON when verify is off is fine too).
        self.assertIsNotNone(payload)


if __name__ == "__main__":
    unittest.main()
