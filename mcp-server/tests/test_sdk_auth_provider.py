# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software: you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT OF MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""CannbotAuthProvider tests: the SDK client-registry methods (ticket 4
SDK auth adapter) and the authorize/token series
(ticket 5). The remaining protocol surface (exchange_identity_assertion,
load_access_token, revoke_token) stays locked as NotImplementedError
stubs until their later tickets."""
import asyncio
import base64
import hashlib
import json
import os
import secrets
import tempfile
import time
import unittest
import urllib.parse
from pathlib import Path

import sdk_auth_provider
import server
import state_store
from mcp.server.auth.provider import (
    AuthorizationParams,
    OAuthClientInformationFull,
    TokenError,
)

PUBLIC_CLIENT_ID = sdk_auth_provider.PUBLIC_CLIENT_ID
GRANT_TYPES = [
    "authorization_code",
    "urn:ietf:params:oauth:grant-type:device_code",
    "refresh_token",
]
RESOURCE_URL = "http://127.0.0.1:8090/mcp"
REDIRECT_URI = "http://localhost:55685/callback"


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


class _ProviderFixture:
    """A provider over a throwaway sqlite StateStore: the same ledgers
    build_http_app owns (AuthCodeStore + jti ledger + token authority),
    at test scope."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._saved_secret = os.environ.get(server.AUTH_SECRET_ENV)
        os.environ[server.AUTH_SECRET_ENV] = "test-secret"
        self.store = state_store.SqliteStateStore(
            Path(self._tmp.name) / "state.db"
        )
        self.auth_code_store = server.AuthCodeStore(self.store)
        self.token_authority = server.SelfIssuedTokenAuthority()
        self.provider = sdk_auth_provider.CannbotAuthProvider(
            self.auth_code_store,
            self.store,
            self.token_authority,
            resource_server_url=RESOURCE_URL,
        )
        self.client = sdk_auth_provider.public_client_information()

    def close(self) -> None:
        self.store.close()
        saved = self._saved_secret
        if saved is None:
            os.environ.pop(server.AUTH_SECRET_ENV, None)
        else:
            os.environ[server.AUTH_SECRET_ENV] = saved
        self._tmp.cleanup()


class CannbotAuthProviderClientRegistryTests(unittest.TestCase):
    """get_client/register_client mirror the /register handler."""

    def setUp(self) -> None:
        # The registry is module-level; snapshot+clear it per test and
        # restore afterwards so tests stay order-independent.
        self._saved = dict(sdk_auth_provider._clients)
        sdk_auth_provider._clients.clear()
        self._fixture = _ProviderFixture()
        self.provider = self._fixture.provider

    def tearDown(self) -> None:
        sdk_auth_provider._clients.clear()
        sdk_auth_provider._clients.update(self._saved)
        self._fixture.close()

    def _assert_fixed_public_client(
        self, info: OAuthClientInformationFull
    ) -> None:
        # The complete field set the /register handler hands out.
        self.assertIsInstance(info, OAuthClientInformationFull)
        self.assertEqual(PUBLIC_CLIENT_ID, info.client_id)
        self.assertEqual(GRANT_TYPES, info.grant_types)
        self.assertEqual("none", info.token_endpoint_auth_method)
        self.assertEqual([], info.redirect_uris)
        self.assertEqual("cannbot-knowledge", info.client_name)
        self.assertIsNotNone(info.client_id_issued_at)
        # Public client: no secret is ever issued.
        self.assertIsNone(info.client_secret)

    def test_register_then_get_returns_complete_public_client(self) -> None:
        # The submitted client_info is accepted and ignored, exactly like
        # the /register handler's POST body.
        submitted = OAuthClientInformationFull(
            client_id="sdk-generated-id", client_name="some-sdk-client"
        )
        self.assertIsNone(
            asyncio.run(self.provider.register_client(submitted))
        )
        stored = asyncio.run(self.provider.get_client(PUBLIC_CLIENT_ID))
        self._assert_fixed_public_client(stored)
        # Retrieval comes from the registry entry register_client wrote.
        self.assertIs(stored, sdk_auth_provider._clients[PUBLIC_CLIENT_ID])
        # The submitted id never becomes a registry key.
        self.assertIsNone(
            asyncio.run(self.provider.get_client("sdk-generated-id"))
        )

    def test_repeated_registration_stays_idempotent(self) -> None:
        for _ in range(2):
            asyncio.run(
                self.provider.register_client(
                    OAuthClientInformationFull(
                        client_id="irrelevant", client_name="x"
                    )
                )
            )
        self.assertEqual([PUBLIC_CLIENT_ID], list(sdk_auth_provider._clients))
        self._assert_fixed_public_client(
            asyncio.run(self.provider.get_client(PUBLIC_CLIENT_ID))
        )

    def test_get_public_client_without_registration(self) -> None:
        # Idempotent path: the fixed description resolves with an empty
        # registry (fresh process, nothing registered yet).
        info = asyncio.run(self.provider.get_client(PUBLIC_CLIENT_ID))
        self._assert_fixed_public_client(info)
        self.assertEqual({}, sdk_auth_provider._clients)

    def test_unknown_client_returns_none(self) -> None:
        self.assertIsNone(asyncio.run(self.provider.get_client("random")))

    def test_later_ticket_stub_methods_raise_not_implemented(self) -> None:
        for name in (
            "exchange_identity_assertion",
            "load_access_token",
            "revoke_token",
        ):
            with self.subTest(method=name):
                with self.assertRaises(NotImplementedError):
                    asyncio.run(getattr(self.provider, name)())


class CannbotAuthProviderAuthSeriesTests(unittest.TestCase):
    """The ticket-5 authorize/token series: code+PKCE exchange, one-shot
    code, one-shot refresh, and the RFC 8707 audience binding."""

    def setUp(self) -> None:
        self._fixture = _ProviderFixture()
        self.provider = self._fixture.provider
        self.client = self._fixture.client
        self.store = self._fixture.store
        self.authority = self._fixture.token_authority

    def tearDown(self) -> None:
        self._fixture.close()

    def _authorize(self, resource: str | None) -> tuple[str, str, str]:
        """authorize() → (code, verifier, challenge); asserts the code
        and state ride back on the client's redirect_uri."""
        verifier, challenge = _pkce()
        params = AuthorizationParams(
            state="st-1",
            scopes=["mcp"],
            code_challenge=challenge,
            redirect_uri=REDIRECT_URI,
            redirect_uri_provided_explicitly=True,
            resource=resource,
        )
        url = asyncio.run(self.provider.authorize(self.client, params))
        parsed = urllib.parse.urlsplit(url)
        self.assertEqual("http", parsed.scheme)
        self.assertEqual("localhost:55685", parsed.netloc)
        self.assertEqual("/callback", parsed.path)
        query = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(["st-1"], query.get("state"))
        return query["code"][0], verifier, challenge

    def _load_for_exchange(
        self, code: str, verifier: str
    ) -> sdk_auth_provider.CannbotAuthorizationCode:
        loaded = asyncio.run(
            self.provider.load_authorization_code(self.client, code)
        )
        self.assertIsNotNone(loaded)
        return loaded.model_copy(update={"code_verifier": verifier})

    def _grant(self, resource: str | None):
        return asyncio.run(
            self.provider.exchange_authorization_code(
                self.client, self._load_for_exchange(*self._authorize(resource)[:2])
            )
        )

    def test_authorize_binds_code_and_loads_full_session(self) -> None:
        resource = "https://knowledge.internal.example.com"
        code, verifier, challenge = self._authorize(resource)
        # token_urlsafe(32): >= 128 bits of entropy (RFC 6749 §10.10).
        self.assertGreaterEqual(len(code), 43)
        loaded = asyncio.run(
            self.provider.load_authorization_code(self.client, code)
        )
        self.assertIsNotNone(loaded)
        self.assertEqual(code, loaded.code)
        self.assertEqual(PUBLIC_CLIENT_ID, loaded.client_id)
        self.assertEqual(REDIRECT_URI, str(loaded.redirect_uri))
        self.assertEqual(challenge, loaded.code_challenge)
        self.assertEqual(resource, loaded.resource)
        self.assertEqual(PUBLIC_CLIENT_ID, loaded.subject)
        self.assertGreater(loaded.expires_at, time.time())
        self.assertEqual(["mcp"], loaded.scopes)
        self.assertTrue(loaded.redirect_uri_provided_explicitly)
        # recompute the challenge from the verifier: PKCE-consistent mint
        digest = (
            base64.urlsafe_b64encode(
                hashlib.sha256(verifier.encode()).digest()
            )
            .rstrip(b"=")
            .decode()
        )
        self.assertEqual(digest, loaded.code_challenge)

    def test_exchange_correct_verifier_mints_resource_aud_tokens(self) -> None:
        resource = "https://knowledge.internal.example.com"
        tokens = self._grant(resource)
        self.assertEqual("Bearer", tokens.token_type)
        self.assertGreater(tokens.expires_in, 0)
        self.assertTrue(tokens.access_token)
        self.assertTrue(tokens.refresh_token)
        self.assertEqual(resource, _decode_payload(tokens.access_token)["aud"])
        self.assertEqual(resource, _decode_payload(tokens.refresh_token)["aud"])
        # the fresh refresh id is live in the one-time-use ledger
        jti = _decode_payload(tokens.refresh_token)["jti"]
        self.assertEqual("live", self.store.get(f"jti:{jti}"))

    def test_exchange_without_resource_defaults_to_resource_server_url(
        self,
    ) -> None:
        tokens = self._grant(None)
        self.assertEqual(
            RESOURCE_URL, _decode_payload(tokens.access_token)["aud"]
        )
        self.assertEqual(
            RESOURCE_URL, _decode_payload(tokens.refresh_token)["aud"]
        )
        # the fallback-audience pair refreshes on the same audience
        loaded = asyncio.run(
            self.provider.load_refresh_token(self.client, tokens.refresh_token)
        )
        self.assertIsNotNone(loaded)
        self.assertEqual(RESOURCE_URL, loaded.resource)
        refreshed = asyncio.run(
            self.provider.exchange_refresh_token(self.client, loaded, ["mcp"])
        )
        self.assertEqual(
            RESOURCE_URL, _decode_payload(refreshed.access_token)["aud"]
        )

    def test_exchange_wrong_verifier_rejected(self) -> None:
        code, verifier, _challenge = self._authorize(None)
        loaded = asyncio.run(
            self.provider.load_authorization_code(self.client, code)
        )
        wrong = loaded.model_copy(update={"code_verifier": "wrong" * 12})
        with self.assertRaises(TokenError) as ctx:
            asyncio.run(
                self.provider.exchange_authorization_code(self.client, wrong)
            )
        self.assertEqual("invalid_grant", ctx.exception.error)
        # the take happens before validation, so the failed exchange
        # burns the code — even the correct verifier cannot retry it
        retry = loaded.model_copy(update={"code_verifier": verifier})
        with self.assertRaises(TokenError) as retry_ctx:
            asyncio.run(
                self.provider.exchange_authorization_code(self.client, retry)
            )
        self.assertEqual("invalid_grant", retry_ctx.exception.error)

    def test_code_replay_rejected(self) -> None:
        code, verifier, _challenge = self._authorize(None)
        presented = self._load_for_exchange(code, verifier)
        first = asyncio.run(
            self.provider.exchange_authorization_code(self.client, presented)
        )
        self.assertTrue(first.access_token)
        # one-shot: the stored grant is gone, replay finds nothing
        self.assertIsNone(
            asyncio.run(
                self.provider.load_authorization_code(self.client, code)
            )
        )
        with self.assertRaises(TokenError) as ctx:
            asyncio.run(
                self.provider.exchange_authorization_code(
                    self.client, presented
                )
            )
        self.assertEqual("invalid_grant", ctx.exception.error)

    def test_refresh_once_then_replay_rejected(self) -> None:
        resource = "https://knowledge.internal.example.com"
        tokens = self._grant(resource)
        old_refresh = tokens.refresh_token
        loaded = asyncio.run(
            self.provider.load_refresh_token(self.client, old_refresh)
        )
        self.assertIsNotNone(loaded)
        self.assertEqual(PUBLIC_CLIENT_ID, loaded.client_id)
        self.assertEqual(resource, loaded.resource)
        self.assertEqual(PUBLIC_CLIENT_ID, loaded.subject)
        self.assertGreater(loaded.expires_at or 0, time.time())
        refreshed = asyncio.run(
            self.provider.exchange_refresh_token(self.client, loaded, ["mcp"])
        )
        self.assertNotEqual(old_refresh, refreshed.refresh_token)
        # the rotated pair keeps the same audience (现状 semantics)
        self.assertEqual(
            resource, _decode_payload(refreshed.access_token)["aud"]
        )
        self.assertEqual(
            resource, _decode_payload(refreshed.refresh_token)["aud"]
        )
        # replay of the consumed refresh: both legs reject
        self.assertIsNone(
            asyncio.run(
                self.provider.load_refresh_token(self.client, old_refresh)
            )
        )
        with self.assertRaises(TokenError) as ctx:
            asyncio.run(
                self.provider.exchange_refresh_token(
                    self.client, loaded, ["mcp"]
                )
            )
        self.assertEqual("invalid_grant", ctx.exception.error)
        # the rotated refresh id was booked: usable exactly once more
        reloaded = asyncio.run(
            self.provider.load_refresh_token(
                self.client, refreshed.refresh_token
            )
        )
        self.assertIsNotNone(reloaded)
        again = asyncio.run(
            self.provider.exchange_refresh_token(
                self.client, reloaded, ["mcp"]
            )
        )
        self.assertNotEqual(refreshed.refresh_token, again.refresh_token)

    def test_load_authorization_code_unknown_returns_none(self) -> None:
        self.assertIsNone(
            asyncio.run(
                self.provider.load_authorization_code(
                    self.client, "no-such-code"
                )
            )
        )

    def test_load_refresh_token_rejects_garbage_and_access_type(self) -> None:
        self.assertIsNone(
            asyncio.run(
                self.provider.load_refresh_token(
                    self.client, "garbage-token"
                )
            )
        )
        # a well-signed access token is not a refresh token, and its jti
        # was never booked into the refresh ledger
        access, _ = self.authority.sign("someone", "access", RESOURCE_URL)
        self.assertIsNone(
            asyncio.run(self.provider.load_refresh_token(self.client, access))
        )


if __name__ == "__main__":
    unittest.main()
