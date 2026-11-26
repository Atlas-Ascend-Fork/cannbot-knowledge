# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software: you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT OF MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""SDK RS-layer wiring tests (SDK_AUTH=on acceptance locks).

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
    """Acceptance locks for the RS wiring, all under CANNBOT_MCP_SDK_AUTH=on."""

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
        # Both 9728 variants agree: the outer handler answers every probed
        # path (bare and /mcp-suffixed) with the same _sdk_pr_metadata
        # declaration.
        self.assertEqual(bare.json(), variant.json())

    def test_discovery_metadata_carries_cors_headers(self) -> None:
        # Browser-based MCP clients (MCP Inspector and friends) fetch the
        # discovery documents cross-origin; the SDK's own 9728/8414 routes
        # wrap their handlers with allow_origins="*", and this server's
        # outer discovery handlers must keep the same posture. Both GET and
        # the OPTIONS preflight go through the path-matched discovery
        # blocks, so both must answer with Access-Control-Allow-Origin.
        probed = [
            "/.well-known/oauth-protected-resource",
            "/.well-known/oauth-protected-resource/mcp",
            "/.well-known/oauth-authorization-server",
            "/.well-known/oauth-authorization-server/mcp",
        ]
        with self._client() as client:
            for path in probed:
                for method in ("get", "options"):
                    with self.subTest(path=path, method=method):
                        response = getattr(client, method)(path)
                        self.assertEqual(200, response.status_code)
                        self.assertEqual(
                            "*", response.headers.get("access-control-allow-origin")
                        )

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


class PrefixedPublicUrlPrdTests(unittest.TestCase):
    """9728 discovery under a path-prefixed PUBLIC_URL deployment.

    The remote gateway shape: PUBLIC_URL carries a path prefix (a sub-path
    gateway deployment). create_protected_resource_routes registers the
    SDK route at /.well-known/oauth-protected-resource + the resource path
    (prefix + /mcp), so a gateway that strips only its own prefix from
    RFC 9728 insertion URLs delivers the /mcp-suffixed probe to this
    server as the bare +/mcp path. The old pass-through of that path to
    `inner` hit no route there and surfaced as a Starlette 404 — Claude
    Code dies at discovery because the 401's resource_metadata points at
    that very URL. Every probed path must answer with the SDK metadata.
    """

    PREFIXED_PUBLIC_URL = "http://127.0.0.1:9999/mcp/gateway/mcp-server"
    PREFIX = "/mcp/gateway/mcp-server"

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory(prefix="sdk-prd-prefix-")
        cls._saved = {
            name: os.environ.get(name)
            for name in (
                server.SDK_AUTH_ENV,
                PUBLIC_URL_ENV,
                server.PUBLIC_PATH_ENV,
                server.AUTH_SECRET_ENV,
                server.AUTH_DB_ENV,
                server.GITCODE_VERIFY_ENV,
                server.LOG_ENV,
            )
        }
        os.environ[server.SDK_AUTH_ENV] = "on"
        os.environ[PUBLIC_URL_ENV] = cls.PREFIXED_PUBLIC_URL
        # Sub-path deployments declare the prefix explicitly (the
        # 3310e225/a5892470 contract); _discovery_paths reads this env
        # at request time.
        os.environ[server.PUBLIC_PATH_ENV] = cls.PREFIX
        os.environ[server.AUTH_SECRET_ENV] = "sdk-prd-prefix-secret"
        os.environ[server.AUTH_DB_ENV] = str(Path(cls._tmp.name) / "auth.db")
        os.environ[server.GITCODE_VERIFY_ENV] = "off"
        os.environ[server.LOG_ENV] = "off"
        importlib.reload(server)
        assert server._SDK_AUTH_SETTINGS is not None

    @classmethod
    def tearDownClass(cls) -> None:
        for name, value in cls._saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        importlib.reload(server)
        assert server._SDK_AUTH_SETTINGS is None
        cls._tmp.cleanup()

    def setUp(self) -> None:
        self.app = server.build_http_app(
            server.mcp_server,
            server.TokenList.parse("cbk_ready:ready"),
            server.SlidingWindowRateLimiter(state_store.open_state_store()),
            server.IpCooldown(state_store.open_state_store()),
            0,
            "127.0.0.1",
        )

    def test_every_probed_9728_path_serves_sdk_metadata(self) -> None:
        resource = self.PREFIXED_PUBLIC_URL + "/mcp"
        issuer = self.PREFIXED_PUBLIC_URL
        probed = [
            # Direct (gateway strips its prefix, keeps the suffix).
            "/.well-known/oauth-protected-resource",
            "/.well-known/oauth-protected-resource/mcp",
            # RFC 9728 insertion forms clients derive from the endpoint
            # URL — the suffixed one is what the 401's resource_metadata
            # names and where Claude Code died.
            f"/.well-known/oauth-protected-resource{self.PREFIX}",
            f"/.well-known/oauth-protected-resource{self.PREFIX}/mcp",
        ]
        with TestClient(self.app, base_url="http://127.0.0.1:9999") as client:
            for path in probed:
                with self.subTest(path=path):
                    response = client.get(path)
                    self.assertEqual(200, response.status_code, path)
                    metadata = response.json()
                    self.assertEqual(resource, metadata["resource"])
                    self.assertEqual([issuer], metadata["authorization_servers"])
                    self.assertEqual(["header"], metadata["bearer_methods_supported"])

    def test_prefixed_discovery_metadata_carries_cors_headers(self) -> None:
        # The prefixed deployment's discovery responses keep the same CORS
        # posture as the bare deployment (and the SDK's own routes):
        # browser clients must read the metadata cross-origin on every
        # probed path, GET and OPTIONS preflight alike.
        probed = [
            "/.well-known/oauth-protected-resource/mcp",
            f"/.well-known/oauth-protected-resource{self.PREFIX}/mcp",
            f"/.well-known/oauth-authorization-server{self.PREFIX}",
            f"/.well-known/oauth-authorization-server{self.PREFIX}/mcp",
        ]
        with TestClient(self.app, base_url="http://127.0.0.1:9999") as client:
            for path in probed:
                for method in ("get", "options"):
                    with self.subTest(path=path, method=method):
                        response = getattr(client, method)(path)
                        self.assertEqual(200, response.status_code, path)
                        self.assertEqual(
                            "*", response.headers.get("access-control-allow-origin")
                        )


if __name__ == "__main__":
    unittest.main()
