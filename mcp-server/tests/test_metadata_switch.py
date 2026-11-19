"""Metadata switch and fallback tests."""
import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path

import server
import state_store


class MetadataSwitchTests(unittest.TestCase):
    """Self-hosted AS metadata by default; AUTH_SERVER=off falls back."""

    def _app(self) -> object:
        async def stub_inner(scope, receive, send) -> None:
            raise AssertionError("metadata paths must not reach the MCP app")

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

    def _get(self, path: str, method: str = "GET") -> tuple[int, dict]:
        async def receive() -> dict:
            return {"type": "http.request", "body": b"", "more_body": False}

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
        asyncio.run(self.app(scope, receive, send))
        status = sent[0]["status"] if sent else None
        payload = b"".join(
            m.get("body", b"") for m in sent if m["type"] == "http.response.body"
        )
        return status, json.loads(payload) if payload else {}

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        env_keys = (
            server.AUTH_DB_ENV,
            server.AUTH_SECRET_ENV,
            server.AUTH_SERVER_ENV,
            server.OAUTH_CLIENT_ID_ENV,
            server.OAUTH_CLIENT_SECRET_ENV,
        )
        self._saved = {k: os.environ.get(k) for k in env_keys}
        os.environ[server.AUTH_DB_ENV] = str(Path(self._tmp.name) / "auth.db")
        os.environ[server.AUTH_SECRET_ENV] = "test-secret"
        os.environ[server.OAUTH_CLIENT_ID_ENV] = "cid_test"
        os.environ[server.OAUTH_CLIENT_SECRET_ENV] = "sec_test"
        os.environ.pop(server.AUTH_SERVER_ENV, None)
        self.app = self._app()

    def tearDown(self) -> None:
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self._tmp.cleanup()

    def test_self_hosted_metadata_by_default(self) -> None:
        status, metadata = self._get("/.well-known/oauth-authorization-server")
        self.assertEqual(200, status)
        # No Host header in the test scope: _public_url falls back to
        # its server-address default; the issuer simply IS that URL.
        self.assertTrue(metadata["issuer"].startswith("http://"))
        self.assertTrue(metadata["device_authorization_endpoint"].startswith(metadata["issuer"]))
        self.assertIn(
            "urn:ietf:params:oauth:grant-type:device_code",
            metadata["grant_types_supported"],
        )
        self.assertIn("refresh_token", metadata["grant_types_supported"])
        self.assertTrue(
            metadata["device_authorization_endpoint"].endswith("/oauth/device/code")
        )
        self.assertTrue(metadata["token_endpoint"].endswith("/oauth/device/token"))
        self.assertTrue(metadata["registration_endpoint"].endswith("/register"))
        self.assertIn("S256", metadata["code_challenge_methods_supported"])
        self.assertEqual(["none"], metadata["token_endpoint_auth_methods_supported"])

    def test_register_public_client_in_self_hosted_mode(self) -> None:
        status, body = self._get("/register", method="POST")
        self.assertEqual(200, status)
        self.assertEqual("cannbot-knowledge-public", body["client_id"])
        self.assertEqual("none", body["token_endpoint_auth_method"])
        self.assertNotIn("client_secret", body)
        self.assertIn(
            "urn:ietf:params:oauth:grant-type:device_code", body["grant_types"]
        )

    def test_fallback_restores_gitcode_forwarding(self) -> None:
        os.environ[server.AUTH_SERVER_ENV] = "off"
        status, metadata = self._get("/.well-known/oauth-authorization-server")
        self.assertEqual(200, status)
        self.assertEqual("https://gitcode.com", metadata["issuer"])
        self.assertEqual(
            "https://gitcode.com/oauth/authorize", metadata["authorization_endpoint"]
        )
        self.assertEqual(
            "https://gitcode.com/oauth/token", metadata["token_endpoint"]
        )
        self.assertIn("authorization_code", metadata["grant_types_supported"])
        self.assertNotIn("device_authorization_endpoint", metadata)
        # Forwarding-mode /register is closed and NOT advertised: the only
        # thing it could return is the shared application secret.
        self.assertNotIn("registration_endpoint", metadata)
        status, body = self._get("/register", method="POST")
        self.assertEqual(404, status)
        self.assertNotIn("client_secret", body)

    def test_device_endpoints_work_in_both_modes(self) -> None:
        for mode in (None, "off"):
            with self.subTest(mode=mode):
                if mode is None:
                    os.environ.pop(server.AUTH_SERVER_ENV, None)
                else:
                    os.environ[server.AUTH_SERVER_ENV] = mode
                status, body = self._get("/oauth/device/code", method="POST")
                if mode is None:
                    self.assertEqual(200, status)
                    self.assertIn("device_code", body)
                else:
                    # Closing the self-hosted AS closes its issuance
                    # endpoints too — not just the discovery metadata.
                    self.assertEqual(404, status)

    def test_as_off_closes_as_endpoints_end_to_end(self) -> None:
        os.environ[server.AUTH_SERVER_ENV] = "off"
        for path in (
            "/oauth/device/code",
            "/oauth/device/token",
            "/oauth/authorize",
            "/oauth/authorize/confirm",
            "/activate",
            "/api/keys",
            "/oauth/gitcode/login",
            "/oauth/gitcode/callback",
        ):
            with self.subTest(path=path):
                status, _body = self._get(path, method="POST")
                self.assertEqual(404, status)

    def test_as_off_stops_jwt_and_api_key_acceptance_at_mcp(self) -> None:
        # An AS-issued access JWT and an API key must both stop working
        # once the self-hosted AS is off: closing the AS closes issuance
        # AND acceptance.
        os.environ.pop(server.AUTH_SERVER_ENV, None)
        authority = server.SelfIssuedTokenAuthority()
        access, _ttl = authority.sign("jwt-user", "access", audience="http://localhost")
        sent: list[dict] = []

        async def stub_inner(scope, receive, send) -> None:
            sent.append({"reached": True})

        class StubMcpServer:
            def streamable_http_app(self, **_kwargs: object) -> object:
                return stub_inner

        app = server.build_http_app(
            StubMcpServer(),
            server.TokenList.parse("cbk_ready:ready"),
            server.SlidingWindowRateLimiter(state_store.open_state_store()),
            server.IpCooldown(state_store.open_state_store()),
            0,
            "127.0.0.1",
        )

        async def receive() -> dict:
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message: dict) -> None:
            sent.append(message)

        def run(token: str) -> list[dict]:
            sent.clear()
            scope = {
                "type": "http",
                "method": "POST",
                "path": "/mcp",
                "headers": [(b"authorization", f"Bearer {token}".encode("ascii"))],
                "client": ("10.8.8.9", 44445),
            }
            asyncio.run(app(scope, receive, send))
            return list(sent)

        events = run(access)
        self.assertTrue(any(e.get("reached") for e in events), "JWT accepted while AS on")
        os.environ[server.AUTH_SERVER_ENV] = "off"
        try:
            events = run(access)
            self.assertFalse(
                any(e.get("reached") for e in events),
                "JWT must be rejected once the AS is off",
            )
            statuses = [e.get("status") for e in events if "status" in e]
            self.assertIn(401, statuses)
            events = run("cbk_live_deadbeef_notarealkey")
            self.assertFalse(
                any(e.get("reached") for e in events),
                "API key track must be closed once the AS is off",
            )
        finally:
            os.environ.pop(server.AUTH_SERVER_ENV, None)

    def test_self_hosted_metadata_independent_of_gitcode_track(self) -> None:
        # GITCODE_VERIFY=off turns off the /mcp GitCode verification track
        # only; the self-hosted AS discovery documents must stay up.
        os.environ[server.GITCODE_VERIFY_ENV] = "off"
        try:
            status, metadata = self._get("/.well-known/oauth-authorization-server")
            self.assertEqual(200, status)
            self.assertTrue(metadata["issuer"].startswith("http://"))
            self.assertTrue(
                metadata["device_authorization_endpoint"].endswith("/oauth/device/code")
            )
            status, body = self._get("/register", method="POST")
            self.assertEqual(200, status)
            self.assertEqual("cannbot-knowledge-public", body["client_id"])
            status, _body = self._get("/.well-known/oauth-protected-resource")
            self.assertEqual(200, status)
        finally:
            os.environ.pop(server.GITCODE_VERIFY_ENV, None)

    def test_all_tracks_off_404s_discovery(self) -> None:
        # Static-token-only mode: nothing dynamic to advertise.
        os.environ[server.AUTH_SERVER_ENV] = "off"
        os.environ[server.GITCODE_VERIFY_ENV] = "off"
        try:
            for path in (
                "/.well-known/oauth-protected-resource",
                "/.well-known/oauth-authorization-server",
                "/register",
            ):
                with self.subTest(path=path):
                    status, _body = self._get(path)
                    self.assertEqual(404, status)
        finally:
            os.environ.pop(server.AUTH_SERVER_ENV, None)
            os.environ.pop(server.GITCODE_VERIFY_ENV, None)


if __name__ == "__main__":
    unittest.main()
