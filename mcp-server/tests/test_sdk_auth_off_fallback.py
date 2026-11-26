# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software: you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT OF MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Ticket 8 locks: the handwritten auth chain stays as the fallback.

The SDK-auth migration phase 3 was re-scoped by ticket 8: the
handwritten 9728/8414, /oauth/authorize, /oauth/authorize/confirm,
/oauth/device/token grant bodies and /register handlers are KEPT as the
CANNBOT_MCP_SDK_AUTH=off (default, fallback) implementation instead of
being deleted, so reverting the env keeps the full legacy surface.
These tests lock that contract: the default env keeps the legacy wiring,
SDK_AUTH=on without CANNBOT_MCP_PUBLIC_URL fails closed onto the same
chain, the legacy AS surface still serves end to end (register ->
authorize -> confirm -> token grants -> metadata -> /mcp admission,
with the base-URL resource identity whose change invalidates tokens in
SDK mode), the only physical deletion is the dead
_resolve_knowledge_root helper, and the auth-layer files compile with
warnings as errors.
"""
import asyncio
import base64
import hashlib
import importlib
import json
import os
import secrets
import subprocess
import sys
import tempfile
import unittest
import urllib.parse
from pathlib import Path

import server
import state_store

PUBLIC_URL_ENV = "CANNBOT_MCP_PUBLIC_URL"
PUBLIC_URL = "http://127.0.0.1:9999"
STATIC_TOKEN_ENTRY = "cbk_ready:ready"  # parsed as token "cbk_ready"
STATIC_TOKEN = "cbk_ready"
REDIRECT_URI = "http://localhost:55685/callback"

_SDK_SINGLETONS = (
    "_SDK_TOKEN_AUTHORITY",
    "_SDK_AUTH_SETTINGS",
    "_SDK_TOKEN_VERIFIER",
    "_SDK_TOKEN_STORE",
    "_SDK_AUTH_CODE_STORE",
    "_SDK_AUTH_PROVIDER",
    "_SDK_AUTHORIZE_PAGE",
)


def _pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    return verifier, challenge


def _form(fields: dict) -> bytes:
    return urllib.parse.urlencode(fields).encode()


def _decode_payload(token: str) -> dict:
    body_b = token.split(".")[1]
    padding = "=" * (-len(body_b) % 4)
    return json.loads(base64.urlsafe_b64decode(body_b + padding))


class DefaultOffWiringTests(unittest.TestCase):
    """CANNBOT_MCP_SDK_AUTH default stays empty (off): legacy wiring."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._saved = {
            name: os.environ.get(name)
            for name in (server.SDK_AUTH_ENV, PUBLIC_URL_ENV)
        }
        os.environ.pop(server.SDK_AUTH_ENV, None)
        os.environ.pop(PUBLIC_URL_ENV, None)
        importlib.reload(server)

    @classmethod
    def tearDownClass(cls) -> None:
        for name, value in cls._saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        importlib.reload(server)

    def test_default_env_keeps_handwritten_wiring(self) -> None:
        self.assertFalse(server._sdk_auth_enabled())
        for attr in _SDK_SINGLETONS:
            self.assertIsNone(getattr(server, attr), attr)
        self.assertEqual((), server._SDK_FEATURE_ENDPOINTS)
        self.assertIsNone(server.mcp_server.settings.auth)
        self.assertIsNone(server.mcp_server._token_verifier)
        self.assertIsNone(server.mcp_server._auth_server_provider)

    def test_dead_knowledge_root_helper_physically_removed(self) -> None:
        # Ticket 8's only physical deletion: _resolve_knowledge_root had
        # no callers left in EITHER mode (build_http_app resolves the
        # knowledge root through its own parameter since the AS refactor).
        self.assertFalse(hasattr(server, "_resolve_knowledge_root"))


class FailClosedWiringTests(unittest.TestCase):
    """SDK_AUTH=on without PUBLIC_URL fails closed onto the legacy chain."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._saved = {
            name: os.environ.get(name)
            for name in (server.SDK_AUTH_ENV, PUBLIC_URL_ENV)
        }
        os.environ[server.SDK_AUTH_ENV] = "on"
        os.environ.pop(PUBLIC_URL_ENV, None)
        # Reload emits the documented "staying on the handwritten auth
        # chain" stderr line; the import-time gate must NOT raise.
        importlib.reload(server)

    @classmethod
    def tearDownClass(cls) -> None:
        for name, value in cls._saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        importlib.reload(server)

    def test_on_without_public_url_stays_on_handwritten_chain(self) -> None:
        # Fail-closed contract (README「授权栈模式」): the SDK stack mounts
        # nothing without an explicit issuer/resource identity, so the
        # handwritten chain keeps serving — the revert path survives a
        # misconfigured rollout, not just a deliberate one.
        for attr in _SDK_SINGLETONS:
            self.assertIsNone(getattr(server, attr), attr)
        self.assertIsNone(server.mcp_server.settings.auth)
        self.assertIsNone(server.mcp_server._token_verifier)
        self.assertIsNone(server.mcp_server._auth_server_provider)


class HandwrittenFallbackSurfaceTests(unittest.TestCase):
    """The legacy AS surface serves end to end under the default env."""

    def _app(self) -> tuple[object, list[dict]]:
        inner_calls: list[dict] = []

        async def stub_inner(scope: dict, receive: object, send: object) -> None:
            inner_calls.append(scope)

        class StubMcpServer:
            def streamable_http_app(self, **_kwargs: object) -> object:
                return stub_inner

        app = server.build_http_app(
            StubMcpServer(),
            server.TokenList.parse(STATIC_TOKEN_ENTRY),
            server.SlidingWindowRateLimiter(state_store.open_state_store()),
            server.IpCooldown(state_store.open_state_store()),
            0,
            "127.0.0.1",
        )
        return app, inner_calls

    def _request(
        self,
        app: object,
        path: str,
        method: str = "POST",
        body: bytes = b"",
        query: bytes = b"",
        token: str | None = None,
        statuses: tuple = (200, 302, 400),
    ) -> tuple[dict | None, bytes, str | None, dict | None]:
        received: dict = {"done": False, "body": b""}

        async def receive() -> dict:
            return {"type": "http.request", "body": body, "more_body": False}

        sent: list[dict] = []

        async def send(message: dict) -> None:
            sent.append(message)

        headers: list[tuple[bytes, bytes]] = []
        if token is not None:
            headers.append((b"authorization", f"Bearer {token}".encode()))
        scope = {
            "type": "http",
            "method": method,
            "path": path,
            "query_string": query,
            "headers": headers,
            "client": ("10.8.8.8", 44444),
        }
        asyncio.run(app(scope, receive, send))
        start = next(m for m in sent if m.get("type") == "http.response.start")
        status = start["status"]
        location = None
        for name, value in start.get("headers") or []:
            if name == b"location":
                location = value.decode()
        payload = b"".join(
            m.get("body", b"") for m in sent if m["type"] == "http.response.body"
        )
        assert status in statuses, (status, payload[:200])
        try:
            parsed = json.loads(payload)
        except ValueError:
            parsed = None
        return parsed, payload, location, start

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="sdk-off-fallback-")
        names = (
            server.AUTH_DB_ENV,
            server.AUTH_SECRET_ENV,
            server.AUTH_SERVER_ENV,
            server.GITCODE_VERIFY_ENV,
            server.LOG_ENV,
            PUBLIC_URL_ENV,
        )
        self._saved = {name: os.environ.get(name) for name in names}
        os.environ[server.AUTH_DB_ENV] = str(Path(self._tmp.name) / "auth.db")
        os.environ[server.AUTH_SECRET_ENV] = "sdk-off-fallback-secret"
        os.environ.pop(server.AUTH_SERVER_ENV, None)
        os.environ[server.GITCODE_VERIFY_ENV] = "off"
        os.environ[server.LOG_ENV] = "off"
        os.environ[PUBLIC_URL_ENV] = PUBLIC_URL
        self.app, self.inner_calls = self._app()

    def tearDown(self) -> None:
        for name, value in self._saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        self._tmp.cleanup()

    def _start_grant(self) -> tuple[str, str, str]:
        verifier, challenge = _pkce()
        query = urllib.parse.urlencode(
            {
                "response_type": "code",
                "redirect_uri": REDIRECT_URI,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "state": "client-state-123",
            }
        ).encode()
        _, html, _, _ = self._request(
            self.app,
            "/oauth/authorize",
            method="GET",
            query=query,
            statuses=(200,),
        )
        text = html.decode()
        self.assertIn("确认授权", text)
        self.assertNotIn("55685", text)
        marker = "name='code' value='"
        idx = text.index(marker) + len(marker)
        return text[idx : text.index("'", idx)], "client-state-123", verifier

    def test_register_answers_fixed_public_client(self) -> None:
        payload, _, _, start = self._request(self.app, "/register")
        # The handwritten RFC 7591 handler: plain 200 with the fixed
        # public client (the SDK route's 201 minted-id echo is the
        # on-mode marker these fields deliberately differ from).
        self.assertEqual(200, start["status"])
        assert payload is not None
        self.assertEqual("cannbot-knowledge-public", payload["client_id"])
        self.assertEqual("none", payload["token_endpoint_auth_method"])
        self.assertIn(
            "urn:ietf:params:oauth:grant-type:device_code",
            payload["grant_types"],
        )

    def test_authorization_code_roundtrip_with_base_url_audience(self) -> None:
        code, state, verifier = self._start_grant()
        _, _, location, _ = self._request(
            self.app,
            "/oauth/authorize/confirm",
            body=_form(
                {"code": code, "username": "fallback-user", "action": "allow"}
            ),
            statuses=(302,),
        )
        assert location is not None
        self.assertTrue(location.startswith(REDIRECT_URI + "?"), location)
        back = urllib.parse.parse_qs(urllib.parse.urlsplit(location).query)
        self.assertEqual([code], back["code"])
        self.assertEqual([state], back["state"])
        payload, _, _, _ = self._request(
            self.app,
            "/oauth/device/token",
            body=_form(
                {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT_URI,
                    "code_verifier": verifier,
                }
            ),
        )
        assert payload is not None
        self.assertIn("access_token", payload)
        self.assertIn("refresh_token", payload)
        # Off-mode resource identity: the base URL, NOT PUBLIC_URL/mcp —
        # the aud flip that invalidates existing JWTs when SDK mode is
        # switched on (README「授权栈模式」/TROUBLESHOOTING).
        self.assertEqual(PUBLIC_URL, _decode_payload(payload["access_token"])["aud"])
        self.assertEqual(PUBLIC_URL, _decode_payload(payload["refresh_token"])["aud"])
        # One-shot consume.
        replay, _, _, _ = self._request(
            self.app,
            "/oauth/device/token",
            body=_form(
                {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT_URI,
                    "code_verifier": verifier,
                }
            ),
        )
        assert replay is not None
        self.assertEqual("invalid_grant", replay["error"])

    def test_refresh_grant_rotates_on_the_same_endpoint(self) -> None:
        code, _state, verifier = self._start_grant()
        self._request(
            self.app,
            "/oauth/authorize/confirm",
            body=_form(
                {"code": code, "username": "refresh-user", "action": "allow"}
            ),
            statuses=(302,),
        )
        first, _, _, _ = self._request(
            self.app,
            "/oauth/device/token",
            body=_form(
                {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT_URI,
                    "code_verifier": verifier,
                }
            ),
        )
        assert first is not None
        rotated, _, _, _ = self._request(
            self.app,
            "/oauth/device/token",
            body=_form(
                {
                    "grant_type": "refresh_token",
                    "refresh_token": first["refresh_token"],
                }
            ),
        )
        assert rotated is not None
        self.assertNotEqual(first["access_token"], rotated["access_token"])
        self.assertNotEqual(first["refresh_token"], rotated["refresh_token"])
        self.assertEqual(
            PUBLIC_URL, _decode_payload(rotated["access_token"])["aud"]
        )

    def test_as_metadata_declares_handwritten_endpoints(self) -> None:
        payload, _, _, _ = self._request(
            self.app,
            "/.well-known/oauth-authorization-server",
            method="GET",
            statuses=(200,),
        )
        assert payload is not None
        self.assertEqual(PUBLIC_URL, payload["issuer"])
        self.assertEqual(
            f"{PUBLIC_URL}/oauth/authorize", payload["authorization_endpoint"]
        )
        self.assertEqual(
            f"{PUBLIC_URL}/oauth/device/token", payload["token_endpoint"]
        )
        self.assertEqual(f"{PUBLIC_URL}/register", payload["registration_endpoint"])
        self.assertEqual(
            f"{PUBLIC_URL}/oauth/device/code",
            payload["device_authorization_endpoint"],
        )

    def test_pr_metadata_resource_is_base_public_url(self) -> None:
        payload, _, _, _ = self._request(
            self.app,
            "/.well-known/oauth-protected-resource",
            method="GET",
            statuses=(200,),
        )
        assert payload is not None
        self.assertEqual(PUBLIC_URL, payload["resource"])
        self.assertEqual([PUBLIC_URL], payload["authorization_servers"])

    def test_discovery_metadata_carries_cors_headers(self) -> None:
        # The handwritten (SDK_AUTH=off) discovery endpoints keep the same
        # CORS posture the SDK's own routes carry: browser clients must
        # read the metadata cross-origin, GET and OPTIONS preflight alike.
        for path in (
            "/.well-known/oauth-protected-resource",
            "/.well-known/oauth-protected-resource/mcp",
            "/.well-known/oauth-authorization-server",
            "/.well-known/oauth-authorization-server/mcp",
        ):
            for method in ("GET", "OPTIONS"):
                with self.subTest(path=path, method=method):
                    _, _, _, start = self._request(
                        self.app, path, method=method, statuses=(200,)
                    )
                    header_map = {
                        name.decode("latin-1").lower(): value.decode("latin-1")
                        for name, value in start.get("headers") or []
                    }
                    self.assertEqual(
                        "*", header_map.get("access-control-allow-origin")
                    )
                    self.assertIn(
                        "MCP-Protocol-Version",
                        header_map.get("access-control-allow-headers", ""),
                    )

    def test_mcp_admission_via_handwritten_chain(self) -> None:
        # Wrong bearer: 401 with the RFC 6750 + RFC 9728 hint header.
        _, _, _, start = self._request(
            self.app, "/mcp", token="definitely-wrong", statuses=(401,)
        )
        self.assertEqual(401, start["status"])
        header_names = {
            name.decode("latin-1").lower() for name, _ in start["headers"]
        }
        self.assertIn("www-authenticate", header_names)
        self.assertEqual([], self.inner_calls)
        # Static token track still admits through the handwritten chain.
        # The stub MCP app never sends a response back, so drive the ASGI
        # interface directly and assert the request REACHED it.
        async def receive() -> dict:
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message: dict) -> None:
            pass

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/mcp",
            "query_string": b"",
            "headers": [
                (b"authorization", f"Bearer {STATIC_TOKEN}".encode())
            ],
            "client": ("10.8.8.8", 44444),
        }
        asyncio.run(self.app(scope, receive, send))
        self.assertEqual(1, len(self.inner_calls))


class CompileWarningsTests(unittest.TestCase):
    """Acceptance: the auth-layer files compile with warnings as errors."""

    def test_auth_layer_compiles_with_warnings_as_errors(self) -> None:
        root = Path(__file__).resolve().parent.parent
        files = [
            "server.py",
            "auth_pages.py",
            "sdk_auth_provider.py",
            "sdk_auth_verifier.py",
        ]
        result = subprocess.run(
            [sys.executable, "-W", "error", "-m", "py_compile"]
            + [str(root / name) for name in files],
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
