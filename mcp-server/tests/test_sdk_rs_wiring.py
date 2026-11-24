# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software: you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT OF MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""SDK RS-layer wiring tests (ticket 3 of the SDK auth migration).

MCPServer(auth=AuthSettings, token_verifier=CannbotTokenVerifier) behind
CANNBOT_MCP_SDK_AUTH=on, driven end to end through build_http_app with the
real (reloaded) SDK-wired MCPServer: RFC 9728 metadata switches to the SDK
declaration with resource = the full endpoint URL, and /mcp admission moves
to the SDK bearer middleware, so tokens audience-bound to the bare base
address stop working while resource-bound ones pass.

The SDK-off default is locked by the existing suites (test_server.py et
al.); this module only reloads server with the switch on and restores the
module state in tearDownClass so later suites see the default wiring.
"""
import importlib
import os
import tempfile
import unittest
from pathlib import Path

import server
import state_store
from starlette.testclient import TestClient

PUBLIC_URL_ENV = "CANNBOT_MCP_PUBLIC_URL"
PUBLIC_URL = "http://127.0.0.1:9999"
RESOURCE_URL = PUBLIC_URL + "/mcp"
INITIALIZE_BODY = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "sdk-rs-wiring-test", "version": "0"},
    },
}


class SdkRsWiringTests(unittest.TestCase):
    """Acceptance locks for ticket 3, all under CANNBOT_MCP_SDK_AUTH=on."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory(prefix="sdk-rs-wiring-")
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
        os.environ[server.AUTH_SECRET_ENV] = "sdk-rs-wiring-secret"
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
        # own token authority instead of sharing the reload's instance.
        importlib.reload(server)
        assert server._SDK_AUTH_SETTINGS is None
        assert server.mcp_server.settings.auth is None
        assert server.mcp_server._token_verifier is None
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

    def _initialize(self, client: TestClient, token: str | None) -> object:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        return client.post("/mcp", json=INITIALIZE_BODY, headers=headers)

    def test_module_wiring_binds_settings_and_shared_authority(self) -> None:
        self.assertIsNotNone(server._SDK_AUTH_SETTINGS)
        self.assertEqual(RESOURCE_URL, str(server._SDK_AUTH_SETTINGS.resource_server_url))
        self.assertEqual(PUBLIC_URL, str(server._SDK_AUTH_SETTINGS.issuer_url))
        self.assertTrue(server._SDK_AUTH_SETTINGS.validate_token_resource)
        self.assertIsNotNone(server._SDK_TOKEN_VERIFIER)
        # The authority the adapter verifies with is the module-level one
        # build_http_app shares (single key/audience source).
        self.assertIs(server._SDK_TOKEN_AUTHORITY, server._SDK_TOKEN_VERIFIER._token_authority)

    def test_protected_resource_metadata_is_sdk_style_full_endpoint(self) -> None:
        with self._client() as client:
            bare = client.get("/.well-known/oauth-protected-resource")
            variant = client.get("/.well-known/oauth-protected-resource/mcp")
        for response in (bare, variant):
            self.assertEqual(200, response.status_code)
            metadata = response.json()
            # RFC defect 1.3 fixed: resource is the FULL endpoint URL, not
            # the bare base address.
            self.assertEqual(RESOURCE_URL, metadata["resource"])
            # SDK style: the full ProtectedResourceMetadata field set
            # (mirrored for the bare path from the same AuthSettings).
            self.assertEqual(["header"], metadata["bearer_methods_supported"])
            self.assertEqual(
                [str(server._SDK_AUTH_SETTINGS.issuer_url)],
                metadata["authorization_servers"],
            )
        # Both 9728 variants agree: the /mcp-suffixed one is served by the
        # SDK's own route (passed through to `inner`), the bare one by the
        # outer handler mirroring the same declaration.
        self.assertEqual(bare.json(), variant.json())

    def test_legacy_bare_base_resource_jwt_is_rejected(self) -> None:
        # Tokens audience-bound to the bare base address (the legacy
        # resource identity) are exactly the invalid audience the SDK
        # switch invalidates (RFC §3.1).
        token, _ttl = self.authority.sign("legacy-user", "access", audience=PUBLIC_URL)
        with self._client() as client:
            response = self._initialize(client, token)
        self.assertEqual(401, response.status_code)
        self.assertIn("WWW-Authenticate", response.headers)
        self.assertIn("resource_metadata", response.headers["WWW-Authenticate"])

    def test_full_endpoint_resource_jwt_initialize_succeeds(self) -> None:
        token, _ttl = self.authority.sign("device-user", "access", audience=RESOURCE_URL)
        with self._client() as client:
            response = self._initialize(client, token)
        self.assertEqual(200, response.status_code)
        self.assertIn("cannbot-knowledge", response.text)

    def test_initialize_without_token_is_rejected(self) -> None:
        # The SDK mode /mcp must stay protected: skipping the handwritten
        # chain defers to RequireAuthMiddleware, not to nothing.
        with self._client() as client:
            response = self._initialize(client, None)
        self.assertEqual(401, response.status_code)


if __name__ == "__main__":
    unittest.main()
