# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT OF MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""SDK feature-endpoint mounting tests (ticket 7 of
the SDK auth migration).

Under CANNBOT_MCP_SDK_AUTH=on the endpoints the SDK auth stack lacks —
the device-code pair (/oauth/device/code, /oauth/device/token), the
RFC 8628 user-interaction page (/activate, including the ?code=
one-click direct connect) and the GitCode login legs — are mounted as
custom_starlette_routes on the MCPServer: streamable_http_app() merges
them, and build_http_app's handwritten dispatcher forwards those five
paths to that inner (SDK) app. The handler bodies are the very ones the
SDK-off branches run (extracted to module level and shared through
_AuthLegDeps), so the per-mode difference is the registration, not the
logic; the device-flow pair mints audience-bound to the SDK resource
identity (resource_server_url) so /mcp admission on the SDK bearer
middleware accepts it, and the authorize confirm POST target stays the
handwritten direct store write over the shared AuthCodeStore (ticket 7
noted choice). SDK-off keeps the handwritten routes: the existing
suites (test_device_http, test_gitcode_login, ...) lock that surface
and run against the restored default wiring this module's tearDownClass
reinstalls.
"""
import base64
import importlib
import json
import os
import tempfile
import unittest
import urllib.parse
from pathlib import Path

import server
import state_store
from starlette.testclient import TestClient

PUBLIC_URL_ENV = "CANNBOT_MCP_PUBLIC_URL"
PUBLIC_URL = "http://127.0.0.1:9999"
RESOURCE_URL = PUBLIC_URL + "/mcp"
FEATURE_PATHS = (
    "/oauth/device/code",
    "/oauth/device/token",
    "/activate",
    "/oauth/gitcode/login",
    "/oauth/gitcode/callback",
)
INITIALIZE_BODY = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "sdk-custom-endpoints-test", "version": "0"},
    },
}


def _decode_payload(token: str) -> dict:
    body_b = token.split(".")[1]
    padding = "=" * (-len(body_b) % 4)
    return json.loads(base64.urlsafe_b64decode(body_b + padding))


class SdkCustomEndpointsTests(unittest.TestCase):
    """Acceptance locks for ticket 7, all under CANNBOT_MCP_SDK_AUTH=on."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory(prefix="sdk-custom-eps-")
        cls._saved = {
            name: os.environ.get(name)
            for name in (
                server.SDK_AUTH_ENV,
                PUBLIC_URL_ENV,
                server.AUTH_SECRET_ENV,
                server.AUTH_DB_ENV,
                server.GITCODE_VERIFY_ENV,
                server.LOG_ENV,
                server.OAUTH_CLIENT_ID_ENV,
                server.OAUTH_CLIENT_SECRET_ENV,
            )
        }
        os.environ[server.SDK_AUTH_ENV] = "on"
        os.environ[PUBLIC_URL_ENV] = PUBLIC_URL
        os.environ[server.AUTH_SECRET_ENV] = "sdk-custom-eps-secret"
        os.environ[server.AUTH_DB_ENV] = str(Path(cls._tmp.name) / "auth.db")
        # No outbound track in these tests: the wiring hands the adapter
        # gitcode_verifier=None; the GitCode login exchange is mocked.
        os.environ[server.GITCODE_VERIFY_ENV] = "off"
        os.environ[server.LOG_ENV] = "off"
        # No GitCode application by default: the device flow uses the
        # manual-username allow leg; the direct-connect tests set the
        # client id themselves.
        os.environ.pop(server.OAUTH_CLIENT_ID_ENV, None)
        os.environ.pop(server.OAUTH_CLIENT_SECRET_ENV, None)
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
        # run after this one: the feature-endpoint markers must reset so
        # build_http_app goes back to serving those paths itself.
        importlib.reload(server)
        assert server._SDK_AUTH_SETTINGS is None
        assert server._SDK_AUTH_PROVIDER is None
        assert server._SDK_TOKEN_STORE is None
        assert server.mcp_server.settings.auth is None
        assert server.mcp_server._token_verifier is None
        assert server.mcp_server._auth_server_provider is None
        assert server._SDK_FEATURE_ENDPOINTS == ()
        assert server._SDK_FEATURE_PATHS == frozenset()
        cls._tmp.cleanup()

    def setUp(self) -> None:
        # One app (and therefore one StreamableHTTPSessionManager) per
        # test, like the ticket-6 wiring suite.
        self.app = server.build_http_app(
            server.mcp_server,
            server.TokenList.parse("cbk_ready:ready"),
            server.SlidingWindowRateLimiter(state_store.open_state_store()),
            server.IpCooldown(state_store.open_state_store()),
            0,
            "127.0.0.1",
        )

    def _client(self) -> TestClient:
        return TestClient(self.app, base_url=PUBLIC_URL)

    def _initialize(self, client: TestClient, token: str | None):
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        return client.post("/mcp", json=INITIALIZE_BODY, headers=headers)

    def _new_device(self, client: TestClient) -> dict:
        response = client.post("/oauth/device/code")
        self.assertEqual(200, response.status_code)
        payload = response.json()
        # Same response shape the handwritten endpoint serves (SDK-off
        # suites lock it): page URLs derive from _public_url, i.e.
        # CANNBOT_MCP_PUBLIC_URL here.
        self.assertIn("device_code", payload)
        self.assertIn("user_code", payload)
        self.assertTrue(payload["verification_uri"].endswith("/activate"))
        self.assertEqual(
            f"{PUBLIC_URL}/activate?code={payload['user_code']}",
            payload["verification_uri_complete"],
        )
        self.assertEqual(600, payload["expires_in"])
        self.assertEqual(5, payload["interval"])
        return payload

    def _device_poll(self, client: TestClient, device_code: str):
        return client.post(
            "/oauth/device/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": device_code,
            },
        )

    def _allow_manually(self, client: TestClient, user_code: str, username: str):
        confirm = client.post("/activate", data={"user_code": user_code})
        self.assertEqual(200, confirm.status_code)
        self.assertIn(user_code, confirm.text)
        allowed = client.post(
            "/activate",
            data={
                "user_code": user_code,
                "username": username,
                "action": "allow",
            },
        )
        self.assertEqual(200, allowed.status_code)
        self.assertIn(username, allowed.text)
        return allowed

    def test_feature_endpoints_registered_as_custom_routes(self) -> None:
        # The ticket's mounting: MCPServer custom_starlette_routes (what
        # custom_route() appends and streamable_http_app merges), not
        # more branches in the handwritten dispatcher.
        routes = server.mcp_server._custom_starlette_routes
        by_path = {route.path: route for route in routes}
        for path in FEATURE_PATHS:
            self.assertIn(path, by_path)
            self.assertIn(by_path[path].endpoint, server._SDK_FEATURE_ENDPOINTS)
            self.assertIn("GET", by_path[path].methods)
            self.assertIn("POST", by_path[path].methods)
        self.assertEqual(frozenset(FEATURE_PATHS), server._SDK_FEATURE_PATHS)
        # The consent page from ticket 6 still rides the same mechanism.
        self.assertIn("/authorize", by_path)

    def test_dispatcher_forwards_feature_paths_to_inner(self) -> None:
        # Behavioural proof the handwritten dispatcher yields these paths
        # to the inner (SDK) app: a method the custom routes do not list
        # answers Starlette's 405, which the handwritten legs (no method
        # check — they would happily mint a device grant) can never
        # produce.
        with self._client() as client:
            response = client.delete("/oauth/device/code")
        self.assertEqual(405, response.status_code)

    def test_device_flow_full_roundtrip(self) -> None:
        with self._client() as client:
            device = self._new_device(client)
            # pending on first poll
            pending = self._device_poll(client, device["device_code"])
            self.assertEqual(400, pending.status_code)
            self.assertEqual(
                "authorization_pending", pending.json()["error"]
            )
            # activate: confirm page, then allow with a manual username
            self._allow_manually(client, device["user_code"], "device-user")
            # poll succeeds and hands out the pair exactly once
            granted = self._device_poll(client, device["device_code"])
            self.assertEqual(200, granted.status_code)
            tokens = granted.json()
            self.assertEqual("Bearer", tokens["token_type"])
            self.assertGreater(tokens["expires_in"], 0)
            # RFC 8707 on the SDK stack: the pair is audience-bound to
            # the resource identity the SDK stack serves under — the
            # thing /mcp admission compares against.
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
            # one-shot: polling again after success no longer yields tokens
            replay = self._device_poll(client, device["device_code"])
            self.assertEqual(400, replay.status_code)
            self.assertEqual("expired_token", replay.json()["error"])

    def test_device_refresh_rides_sdk_token_endpoint(self) -> None:
        with self._client() as client:
            device = self._new_device(client)
            self._allow_manually(client, device["user_code"], "dev-refresh")
            tokens = self._device_poll(client, device["device_code"]).json()
            # The custom-route mint registered its refresh id in the
            # shared jti ledger, so the SDK /token refresh grant rotates
            # it (ticket 6's provider path over the same store).
            refreshed = client.post(
                "/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": tokens["refresh_token"],
                    "client_id": "cannbot-knowledge-public",
                },
            )
            self.assertEqual(200, refreshed.status_code)
            rotated = refreshed.json()
            self.assertNotEqual(tokens["access_token"], rotated["access_token"])
            self.assertEqual(
                RESOURCE_URL,
                _decode_payload(rotated["access_token"])["aud"],
            )
            initialized = self._initialize(client, rotated["access_token"])
            self.assertEqual(200, initialized.status_code)
            # One-shot ledger: replaying the consumed refresh is rejected.
            replay = client.post(
                "/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": tokens["refresh_token"],
                    "client_id": "cannbot-knowledge-public",
                },
            )
            self.assertEqual(400, replay.status_code)
            self.assertEqual("invalid_grant", replay.json()["error"])

    def test_handwritten_token_grants_yield_to_sdk_token(self) -> None:
        # Ticket 6 semantics, now served through the custom route: the
        # authorization-code and refresh grants on /oauth/device/token
        # are the SDK /token endpoint's; only the device grant stays.
        with self._client() as client:
            for grant in (
                {
                    "grant_type": "authorization_code",
                    "code": "no-such-code",
                    "redirect_uri": "http://localhost:55685/callback",
                    "code_verifier": "v" * 43,
                },
                {"grant_type": "refresh_token", "refresh_token": "x"},
            ):
                response = client.post("/oauth/device/token", data=grant)
                self.assertEqual(400, response.status_code)
                self.assertEqual(
                    "unsupported_grant_type", response.json()["error"]
                )

    def test_activate_code_direct_connect_302_to_gitcode_login(self) -> None:
        saved_id = os.environ.get(server.OAUTH_CLIENT_ID_ENV)
        os.environ[server.OAUTH_CLIENT_ID_ENV] = "cid_custom_eps"
        try:
            with self._client() as client:
                device = self._new_device(client)
                # One-click direct connect: the terminal prints
                # /activate?code=XXXX-XXXX and the browser goes straight
                # to the GitCode login leg (root-relative 302, the same
                # Location the handwritten leg emits).
                direct = client.get(
                    "/activate",
                    params={"code": device["user_code"]},
                    follow_redirects=False,
                )
                self.assertEqual(302, direct.status_code)
                location = direct.headers["location"]
                self.assertTrue(
                    location.startswith("/oauth/gitcode/login?state="),
                    location,
                )
                self.assertIn(device["user_code"], location)
                # Following it: the login leg also rides the custom
                # routes and points the browser at GitCode with PKCE.
                login = client.get(location, follow_redirects=False)
                self.assertEqual(302, login.status_code)
                authorize = login.headers["location"]
                self.assertTrue(
                    authorize.startswith("https://gitcode.com/oauth/authorize?"),
                    authorize,
                )
                params = dict(
                    urllib.parse.parse_qsl(authorize.split("?", 1)[1])
                )
                self.assertEqual("cid_custom_eps", params["client_id"])
                self.assertEqual(device["user_code"], params["state"])
                self.assertEqual("S256", params["code_challenge_method"])
                self.assertEqual(43, len(params["code_challenge"]))
                self.assertIn(
                    f"{PUBLIC_URL}/oauth/gitcode/callback",
                    params["redirect_uri"],
                )
        finally:
            if saved_id is None:
                os.environ.pop(server.OAUTH_CLIENT_ID_ENV, None)
            else:
                os.environ[server.OAUTH_CLIENT_ID_ENV] = saved_id

    def test_gitcode_login_roundtrip_binds_identity(self) -> None:
        # The full GitCode leg through the custom routes: login 302 →
        # (mocked) callback exchange → binding-protected reentry →
        # one-click allow → device tokens → /mcp.
        saved_id = os.environ.get(server.OAUTH_CLIENT_ID_ENV)
        saved_secret = os.environ.get(server.OAUTH_CLIENT_SECRET_ENV)
        os.environ[server.OAUTH_CLIENT_ID_ENV] = "cid_custom_eps"
        os.environ[server.OAUTH_CLIENT_SECRET_ENV] = "sec_custom_eps"
        captured: dict = {}

        class _TokenResponse:
            status_code = 200

            def json(self) -> dict:
                return {"access_token": "gc-access"}

        class _UserResponse:
            status_code = 200

            def json(self) -> dict:
                return {"login": "gitcode-user"}

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

        original_client = server.httpx.AsyncClient
        server.httpx.AsyncClient = _Client  # type: ignore[assignment]
        try:
            with self._client() as client:
                device = self._new_device(client)
                login = client.get(
                    "/oauth/gitcode/login",
                    params={"state": device["user_code"]},
                    follow_redirects=False,
                )
                self.assertEqual(302, login.status_code)
                callback = client.get(
                    "/oauth/gitcode/callback",
                    params={
                        "code": "gc-code",
                        "state": device["user_code"],
                    },
                    follow_redirects=False,
                )
                self.assertEqual(302, callback.status_code)
                back = callback.headers["location"]
                # The verified username never travels in the URL — only
                # the unguessable server-side binding token does.
                self.assertTrue(back.startswith("/activate?code="), back)
                self.assertNotIn("gitcode-user", back)
                self.assertIn("st=", back)
                self.assertIn(device["user_code"], back)
                # The exchange used the configured credentials and the
                # one-shot PKCE verifier the login leg stored.
                self.assertEqual(
                    "cid_custom_eps", captured["token_form"]["client_id"]
                )
                self.assertEqual(
                    "sec_custom_eps", captured["token_form"]["client_secret"]
                )
                self.assertEqual(
                    64, len(captured["token_form"]["code_verifier"])
                )
                self.assertIn("/api/v5/user", captured["user_url"])
                # Reentry: the confirm page shows the bound identity...
                st = urllib.parse.parse_qs(
                    urllib.parse.urlsplit(back).query
                )["st"][0]
                confirm = client.get(
                    "/activate",
                    params={"code": device["user_code"], "st": st},
                )
                self.assertEqual(200, confirm.status_code)
                self.assertIn("gitcode-user", confirm.text)
                # ...and the allow consumes the binding (one-shot).
                allowed = client.post(
                    "/activate",
                    data={
                        "user_code": device["user_code"],
                        "st": st,
                        "action": "allow",
                    },
                )
                self.assertEqual(200, allowed.status_code)
                self.assertIn("gitcode-user", allowed.text)
                # The device pair then admits /mcp like any other grant.
                tokens = self._device_poll(
                    client, device["device_code"]
                ).json()
                initialized = self._initialize(client, tokens["access_token"])
                self.assertEqual(200, initialized.status_code)
        finally:
            server.httpx.AsyncClient = original_client
            if saved_id is None:
                os.environ.pop(server.OAUTH_CLIENT_ID_ENV, None)
            else:
                os.environ[server.OAUTH_CLIENT_ID_ENV] = saved_id
            if saved_secret is None:
                os.environ.pop(server.OAUTH_CLIENT_SECRET_ENV, None)
            else:
                os.environ[server.OAUTH_CLIENT_SECRET_ENV] = saved_secret

    def test_activate_unknown_code_rejected(self) -> None:
        with self._client() as client:
            response = client.post(
                "/activate", data={"user_code": "ZZZZ-ZZZZ"}
            )
        self.assertEqual(200, response.status_code)
        self.assertIn("重新发起", response.text)


if __name__ == "__main__":
    unittest.main()
