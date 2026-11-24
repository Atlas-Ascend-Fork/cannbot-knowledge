# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software: you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT OF MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""SDK AS-layer wiring tests (ticket 6 of the SDK auth migration).

MCPServer(auth=AuthSettings(client_registration_options=...enabled),
auth_server_provider=CannbotAuthProvider) behind CANNBOT_MCP_SDK_AUTH=on,
driven end to end through build_http_app with the real (reloaded)
SDK-wired MCPServer: streamable_http_app() mounts the SDK AS route set,
so POST /register is served by the SDK's RegistrationHandler, the
authorization-code flow runs authorize (custom human consent page, ahead
of the SDK's own /authorize route) -> confirm -> SDK /token exchange ->
/mcp 200, and the refresh grant rides the SDK /token endpoint. The
handwritten /register, /oauth/authorize and /oauth/device/token
auth-code/refresh grants yield in this mode and stay as the
SDK_AUTH=off (fallback) implementation (ticket 8 re-scoped the RFC's
phase-3 deletion to keep them); that fallback surface is locked by
tests/test_sdk_auth_off_fallback.py, and the SDK-off default by the
existing suites (test_server.py et al.), which run against the
restored default wiring this module's tearDownClass reinstalls.
"""
import asyncio
import base64
import hashlib
import importlib
import json
import os
import secrets
import tempfile
import unittest
import urllib.parse
from pathlib import Path

import sdk_auth_provider
import server
import state_store
from starlette.testclient import TestClient

PUBLIC_URL_ENV = "CANNBOT_MCP_PUBLIC_URL"
PUBLIC_URL = "http://127.0.0.1:9999"
RESOURCE_URL = PUBLIC_URL + "/mcp"
PUBLIC_CLIENT_ID = sdk_auth_provider.PUBLIC_CLIENT_ID
REDIRECT_URI = "http://localhost:55685/callback"
INITIALIZE_BODY = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "sdk-as-wiring-test", "version": "0"},
    },
}


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


class SdkAsWiringTests(unittest.TestCase):
    """Acceptance locks for ticket 6, all under CANNBOT_MCP_SDK_AUTH=on."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory(prefix="sdk-as-wiring-")
        cls._saved = {
            name: os.environ.get(name)
            for name in (
                server.SDK_AUTH_ENV,
                PUBLIC_URL_ENV,
                server.AUTH_SECRET_ENV,
                server.AUTH_DB_ENV,
                server.GITCODE_VERIFY_ENV,
                server.LOG_ENV,
            )
        }
        os.environ[server.SDK_AUTH_ENV] = "on"
        os.environ[PUBLIC_URL_ENV] = PUBLIC_URL
        os.environ[server.AUTH_SECRET_ENV] = "sdk-as-wiring-secret"
        os.environ[server.AUTH_DB_ENV] = str(Path(cls._tmp.name) / "auth.db")
        # No outbound track in these tests: the wiring hands the adapter
        # gitcode_verifier=None.
        os.environ[server.GITCODE_VERIFY_ENV] = "off"
        os.environ[server.LOG_ENV] = "off"
        importlib.reload(server)
        cls.authority = server._SDK_TOKEN_AUTHORITY
        assert cls.authority is not None

    @classmethod
    def tearDownClass(cls) -> None:
        for name, value in cls._saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        # Restore the default (SDK-off) module wiring for the suites that
        # run after this one: build_http_app must go back to creating its
        # own token authority and stores instead of sharing the reload's
        # singletons.
        importlib.reload(server)
        assert server._SDK_AUTH_SETTINGS is None
        assert server._SDK_AUTH_PROVIDER is None
        assert server._SDK_TOKEN_STORE is None
        assert server.mcp_server.settings.auth is None
        assert server.mcp_server._token_verifier is None
        assert server.mcp_server._auth_server_provider is None
        cls._tmp.cleanup()

    def setUp(self) -> None:
        # One app (and therefore one StreamableHTTPSessionManager) per
        # test: the SDK session manager cannot be reused after its run()
        # context exits, and each TestClient context enters that lifespan.
        self.app = server.build_http_app(
            server.mcp_server,
            server.TokenList.parse("cbk_ready:ready"),
            server.SlidingWindowRateLimiter(state_store.open_state_store()),
            server.IpCooldown(state_store.open_state_store()),
            0,
            "127.0.0.1",
        )

    def _client(self) -> TestClient:
        # Host with an explicit port: the SDK's DNS-rebinding protection
        # for host 127.0.0.1 allows "127.0.0.1:*" only.
        return TestClient(self.app, base_url=PUBLIC_URL)

    def _initialize(self, client: TestClient, token: str | None):
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        return client.post("/mcp", json=INITIALIZE_BODY, headers=headers)

    def test_module_wiring_mounts_provider_and_wraps_verifier(self) -> None:
        # The ticket's constructor shape: AuthSettings with client
        # registration enabled + auth_server_provider (never a second
        # token_verifier argument - the SDK rejects both together).
        self.assertIsNotNone(server._SDK_AUTH_PROVIDER)
        self.assertIs(server._SDK_AUTH_PROVIDER, server.mcp_server._auth_server_provider)
        self.assertTrue(
            server._SDK_AUTH_SETTINGS.client_registration_options.enabled
        )
        # The provider shares the module-level authority/ledgers the
        # handwritten confirm leg (build_http_app) reuses.
        self.assertIs(
            server._SDK_TOKEN_AUTHORITY,
            server._SDK_AUTH_PROVIDER._token_authority,
        )
        self.assertIs(
            server._SDK_TOKEN_STORE, server._SDK_AUTH_PROVIDER._token_store
        )
        # Token verification rides a ProviderTokenVerifier wrapping the
        # ticket-2 four-track verifier (NOT provider.load_access_token,
        # which is a later ticket's stub).
        verifier = server.mcp_server._token_verifier
        self.assertIsInstance(verifier, server.CannbotProviderTokenVerifier)
        token, _ttl = self.authority.sign("wiring-user", "access", RESOURCE_URL)
        verified = asyncio.run(verifier.verify_token(token))
        self.assertIsNotNone(verified)
        self.assertEqual(RESOURCE_URL, str(verified.resource))

    def test_register_served_by_sdk_route(self) -> None:
        with self._client() as client:
            response = client.post(
                "/register",
                json={
                    "client_name": "sdk-as-wiring-test",
                    "redirect_uris": [REDIRECT_URI],
                    "grant_types": ["authorization_code", "refresh_token"],
                    "response_types": ["code"],
                    "token_endpoint_auth_method": "none",
                },
            )
        # The SDK's RegistrationHandler answers 201 Created (RFC 7591
        # §3.2.1); the ticket's "200" reads as "success", and the
        # handwritten handler's plain 200 is exactly what is skipped here.
        self.assertIn(response.status_code, (200, 201))
        body = response.json()
        # Public client: no secret, no auth.
        self.assertEqual("none", body["token_endpoint_auth_method"])
        self.assertIsNone(body.get("client_secret"))
        self.assertIn("authorization_code", body["grant_types"])
        # SDK-route markers (the handwritten handler answered 200 with the
        # fixed client id and no response_types): the SDK handler echoes
        # its own minted client id and the full registered metadata.
        self.assertNotEqual(PUBLIC_CLIENT_ID, body["client_id"])
        self.assertEqual(["code"], body["response_types"])
        # The registration landed in the provider registry as the fixed
        # public client (register_client accepts and ignores the body).
        registered = asyncio.run(
            server._SDK_AUTH_PROVIDER.get_client(PUBLIC_CLIENT_ID)
        )
        self.assertIsNotNone(registered)
        self.assertEqual(PUBLIC_CLIENT_ID, registered.client_id)

    def test_authorize_custom_page_wins_and_sdk_route_serves_post(self) -> None:
        verifier, challenge = _pkce()
        query = {
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": "client-state-123",
            "client_id": PUBLIC_CLIENT_ID,
        }
        with self._client() as client:
            page = client.get("/authorize", params=query)
            # The custom route wins the GET: the human consent page, not
            # the SDK route's JSON/redirect answer.
            self.assertEqual(200, page.status_code)
            self.assertIn("text/html", page.headers["content-type"])
            self.assertIn("确认授权", page.text)
            self.assertIn("name='code' value='", page.text)
            # The loopback redirect host never leaks into the page.
            self.assertNotIn("55685", page.text)
            # Programmatic POST /authorize still reaches the SDK route
            # (the custom route is GET-only; Starlette keeps scanning past
            # the method-partial match). The fixed public client carries
            # no registered redirect_uris, so the SDK authorize handler
            # answers its JSON invalid_request error - the proof that the
            # SDK route, not our page, served the call.
            programmatic = client.post("/authorize", data=query)
            self.assertEqual(400, programmatic.status_code)
            self.assertEqual(
                "invalid_request", programmatic.json()["error"]
            )

    def _start_grant(self, client: TestClient) -> tuple[str, str, str]:
        """GET /authorize (custom page) -> (code, state, verifier)."""
        verifier, challenge = _pkce()
        query = {
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": "client-state-123",
            "client_id": PUBLIC_CLIENT_ID,
        }
        page = client.get("/authorize", params=query)
        self.assertEqual(200, page.status_code)
        marker = "name='code' value='"
        idx = page.text.index(marker) + len(marker)
        return page.text[idx : page.text.index("'", idx)], "client-state-123", verifier

    def _confirm(self, client: TestClient, code: str, username: str) -> str:
        response = client.post(
            "/oauth/authorize/confirm",
            data={"code": code, "username": username, "action": "allow"},
            follow_redirects=False,
        )
        self.assertEqual(302, response.status_code)
        return response.headers["location"]

    def _exchange(self, client: TestClient, code: str, verifier: str) -> dict:
        response = client.post(
            "/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": PUBLIC_CLIENT_ID,
                "code_verifier": verifier,
            },
        )
        self.assertEqual(200, response.status_code)
        return response.json()

    def test_full_authorization_code_flow(self) -> None:
        with self._client() as client:
            code, state, verifier = self._start_grant(client)
            # Confirm on the self-rendered page (handwritten leg over the
            # shared AuthCodeStore): identity binds, the bounce carries
            # code+state back to the client's redirect_uri.
            location = self._confirm(client, code, "sdk-flow-user")
            self.assertTrue(location.startswith(REDIRECT_URI + "?"), location)
            back = urllib.parse.parse_qs(
                urllib.parse.urlsplit(location).query
            )
            self.assertEqual([code], back["code"])
            self.assertEqual([state], back["state"])
            # Exchange on the SDK /token route: the provider consumes the
            # SAME store session the custom page minted.
            tokens = self._exchange(client, code, verifier)
            self.assertEqual("Bearer", tokens["token_type"])
            self.assertTrue(tokens["access_token"])
            self.assertTrue(tokens["refresh_token"])
            self.assertGreater(tokens["expires_in"], 0)
            # RFC 8707: the minted pair is audience-bound to the resource
            # identity the SDK stack serves under.
            self.assertEqual(
                RESOURCE_URL, _decode_payload(tokens["access_token"])["aud"]
            )
            self.assertEqual(
                RESOURCE_URL, _decode_payload(tokens["refresh_token"])["aud"]
            )
            # End to end: the access token admits the /mcp endpoint.
            initialized = self._initialize(client, tokens["access_token"])
            self.assertEqual(200, initialized.status_code)
            self.assertIn("cannbot-knowledge", initialized.text)
            # One-shot: the SDK exchange burns the code.
            replay = client.post(
                "/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT_URI,
                    "client_id": PUBLIC_CLIENT_ID,
                    "code_verifier": verifier,
                },
            )
            self.assertEqual(400, replay.status_code)
            self.assertEqual("invalid_grant", replay.json()["error"])

    def test_refresh_flow_via_sdk_token_endpoint(self) -> None:
        with self._client() as client:
            code, _state, verifier = self._start_grant(client)
            self._confirm(client, code, "refresh-user")
            tokens = self._exchange(client, code, verifier)
            # The refresh grant rides the SDK /token endpoint: load ->
            # verify -> one-shot ledger consume -> rotate on the same
            # audience.
            response = client.post(
                "/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": tokens["refresh_token"],
                    "client_id": PUBLIC_CLIENT_ID,
                },
            )
            self.assertEqual(200, response.status_code)
            rotated = response.json()
            self.assertNotEqual(tokens["access_token"], rotated["access_token"])
            self.assertNotEqual(
                tokens["refresh_token"], rotated["refresh_token"]
            )
            self.assertEqual(
                RESOURCE_URL,
                _decode_payload(rotated["access_token"])["aud"],
            )
            # The rotated access token still admits /mcp.
            initialized = self._initialize(client, rotated["access_token"])
            self.assertEqual(200, initialized.status_code)
            # One-shot ledger: replaying the consumed refresh is rejected.
            replay = client.post(
                "/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": tokens["refresh_token"],
                    "client_id": PUBLIC_CLIENT_ID,
                },
            )
            self.assertEqual(400, replay.status_code)
            self.assertEqual("invalid_grant", replay.json()["error"])

    def test_handwritten_as_surface_skipped_in_sdk_mode(self) -> None:
        verifier, challenge = _pkce()
        with self._client() as client:
            # The handwritten authorize handler yields in this mode
            # (ticket 8 keeps it as the SDK_AUTH=off fallback): the
            # custom /authorize page is the surface.
            legacy_authorize = client.get(
                "/oauth/authorize",
                params={
                    "response_type": "code",
                    "redirect_uri": REDIRECT_URI,
                    "code_challenge": challenge,
                    "code_challenge_method": "S256",
                    "state": "client-state-123",
                },
            )
            self.assertEqual(404, legacy_authorize.status_code)
            # The handwritten token grants are skipped: the SDK /token
            # route owns the authorization-code and refresh exchanges.
            for grant in (
                {
                    "grant_type": "authorization_code",
                    "code": "no-such-code",
                    "redirect_uri": REDIRECT_URI,
                    "code_verifier": verifier,
                },
                {"grant_type": "refresh_token", "refresh_token": "x"},
            ):
                response = client.post("/oauth/device/token", data=grant)
                self.assertEqual(400, response.status_code)
                self.assertEqual(
                    "unsupported_grant_type", response.json()["error"]
                )

    def test_as_metadata_declares_sdk_endpoints(self) -> None:
        with self._client() as client:
            response = client.get("/.well-known/oauth-authorization-server")
        self.assertEqual(200, response.status_code)
        metadata = response.json()
        self.assertEqual(PUBLIC_URL, metadata["issuer"])
        self.assertEqual(
            f"{PUBLIC_URL}/authorize", metadata["authorization_endpoint"]
        )
        self.assertEqual(f"{PUBLIC_URL}/token", metadata["token_endpoint"])
        self.assertEqual(f"{PUBLIC_URL}/register", metadata["registration_endpoint"])
        # RFC §2.4: the self-managed device-code legs stay declared.
        self.assertEqual(
            f"{PUBLIC_URL}/oauth/device/code",
            metadata["device_authorization_endpoint"],
        )
        self.assertIn(
            "urn:ietf:params:oauth:grant-type:device_code",
            metadata["grant_types_supported"],
        )


if __name__ == "__main__":
    unittest.main()
