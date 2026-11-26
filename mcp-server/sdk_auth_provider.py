# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software: you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT OF MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""SDK OAuthAuthorizationServerProvider adapter: the client-registry
methods (SDK auth adapter) and the
authorize/token series (ticket 5). authorize mints a one-shot
authorization code in the existing AuthCodeStore, the code exchange
enforces PKCE and mints the access/refresh pair through
SelfIssuedTokenAuthority, and the refresh series walks the existing jti
one-time ledger. revoke_token, load_access_token and
exchange_identity_assertion stay NotImplementedError stubs for their
later tickets; mounting this provider on the SDK AS routes is the
wiring ticket's job, so nothing in server.py constructs it yet.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import time

from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    AuthorizeError,
    OAuthAuthorizationServerProvider,
    OAuthClientInformationFull,
    OAuthToken,
    RefreshToken,
    TokenError,
    construct_redirect_uri,
)

import server
import state_store

PUBLIC_CLIENT_ID = "cannbot-knowledge-public"

# In-memory client registry {client_id: (info, expires_at)}. A write-through
# cache over the shared StateStore ledger (key prefix dcr:): registrations
# survive restarts and are visible to every replica behind the load
# balancer, so a /token exchange routed to a different instance (or issued
# after a restart) still resolves the client the SDK's DCR handler minted.
# Cache entries carry the ledger's expiry and are checked on read, so the
# shared ledger stays authoritative — an entry that fell out of its TTL
# window disappears here too instead of lingering in memory.
_CLIENT_REGISTRY_PREFIX = "dcr:"
# Registration retention, deliberately longer than the refresh-token
# lifetime: refresh tokens live 30 days by default and each rotation
# re-issues the full window, so an actively refreshing client outlives a
# 30-day registration record and its next /token exchange would fail with
# invalid_client. 90 days = one full refresh window plus two more for
# rotation slack; a client idle for 90 days re-registers transparently
# (every OAuth client starts with a fresh DCR before authorizing).
_CLIENT_REGISTRY_TTL_S = 90 * 24 * 3600

# Short cache window for entries recovered from the ledger (cache misses on
# this replica): the ledger record may be anywhere inside its TTL window
# and StateStore.get does not expose the remainder, so a recovered entry
# must not assume a fresh full window — one hour of caching still absorbs
# a /register→/authorize→/token burst while keeping the shared ledger
# authoritative over replicas.
_CLIENT_RECOVERY_TTL_S = 3600

_clients: dict[str, tuple[OAuthClientInformationFull, float]] = {}


def public_client_information() -> OAuthClientInformationFull:
    """The fixed public-client registration mirroring the /register
    handler: PKCE public client (no secret, ``token_endpoint_auth_method``
    "none") covering the authorization-code, device-code and refresh
    grants; ``redirect_uris`` are informational only (the device flow has
    no redirect)."""
    return OAuthClientInformationFull(
        client_id=PUBLIC_CLIENT_ID,
        client_id_issued_at=int(time.time()),
        redirect_uris=[],
        grant_types=[
            "authorization_code",
            "urn:ietf:params:oauth:grant-type:device_code",
            "refresh_token",
        ],
        token_endpoint_auth_method="none",
        client_name="cannbot-knowledge",
    )


class CannbotAuthorizationCode(AuthorizationCode):
    """AuthorizationCode carrying an AuthCodeStore session on the SDK
    surface, plus the token request's PKCE ``code_verifier`` when the
    caller can supply it.

    The SDK token handler validates ``S256(verifier)`` against
    ``code_challenge`` itself (mcp/server/auth/handlers/token.py) and
    then hands the provider exactly the object ``load_authorization_code``
    returned, so through the SDK route the verifier never reaches
    ``exchange_authorization_code``. ``code_verifier`` is the field for
    callers that do have it (tests today, any later bridging): exchange
    then re-runs the full S256 check against the stored challenge. Left
    empty, exchange still compares the presented ``code_challenge``
    with the authorize-time one — under the SDK that comparison closes
    the PKCE chain transitively, because the handler already proved
    ``S256(verifier) == presented challenge``.
    """

    code_verifier: str = ""


def _s256_digest(verifier: str) -> str:
    """RFC 7636 §4.2 S256 challenge digest — the same computation
    ``AuthCodeStore.consume`` runs."""
    return (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )


def _jwt_payload(token: str) -> dict[str, object]:
    """Unverified payload read for the ledger bookkeeping fields
    (``aud``/``exp``/``jti``) of a token that is about to be, or just
    was, signature-checked; mirrors the helper in sdk_auth_verifier."""
    parts = token.split(".")
    if len(parts) != 3:
        return {}
    try:
        payload = json.loads(
            server.SelfIssuedTokenAuthority._b64url_decode(parts[1])
        )
    except (ValueError, binascii.Error):
        return {}
    return payload if isinstance(payload, dict) else {}


class CannbotAuthProvider(
    OAuthAuthorizationServerProvider[
        CannbotAuthorizationCode, RefreshToken, AccessToken
    ]
):
    """SDK ``OAuthAuthorizationServerProvider`` over the existing auth
    ledgers.

    Client registry: register_client persists the SDK DCR handler's
    registration (random client_id) through the shared StateStore ledger
    (``dcr:`` keys, 90-day TTL — longer than the 30-day refresh window so
    actively rotating clients never outlive their registration), so
    registrations survive restarts and are visible to every replica;
    get_client resolves the TTL-checked in-memory cache, then the ledger,
    and the fixed public client id also resolves
    without prior registration. The
    authorize/token series rides the ledgers server.py
    already owns:

    - authorize mints the one-shot code with ``AuthCodeStore.create``
      (redirect_uri / code_challenge / state / resource bound at mint)
      and immediately ``bind``s it, so the grant is complete when the
      code is handed back. The resource owner bound is the fixed public
      client's id — the interim identity available without a login leg
      (the consent/GitCode-login pages mount with the later custom-routes
      wiring ticket and will bind the verified username there instead,
      exactly like the handwritten /oauth/authorize/confirm leg does).
    - load_authorization_code reads the stored session back (the raw
      store read the handwritten deny leg uses; ``lookup`` cannot serve
      here because it treats a bound session as consumed). None means
      not found — the SDK handler maps that to invalid_grant itself.
    - exchange_authorization_code burns the code one-shot (``take``),
      re-validates the authorize-time bindings (identity, PKCE
      challenge, client, loopback redirect — consume's semantics with
      the challenge the SDK handler already verifier-checked), then
      signs the access/refresh pair with ``token_authority.sign`` for
      ``aud = resource`` or this server's resource URL, and registers
      the fresh refresh id in the jti ledger. Rejections raise
      ``TokenError("invalid_grant")`` — never None-as-error.
    - load_refresh_token verifies the refresh JWT locally (signature,
      typ, exp — anchored on the token's own aud, since the SDK handler
      drops the request's resource indicator) and peeks the jti ledger;
      exchange_refresh_token re-verifies, consumes the id with the
      one-shot ``take_if_equal``, and rotates the pair onto the SAME
      audience (the 现状 semantics of the handwritten refresh grant).
    """

    def __init__(
        self,
        auth_code_store: server.AuthCodeStore,
        token_store: state_store.StateStore,
        token_authority: server.SelfIssuedTokenAuthority,
        resource_server_url: str | None = None,
    ) -> None:
        self._auth_code_store = auth_code_store
        self._token_store = token_store
        self._token_authority = token_authority
        self._resource_server_url = resource_server_url
        # Registration retention must stay ahead of the refresh-token
        # lifetime it protects: refresh TTL is operator-configurable
        # (CANNBOT_MCP_REFRESH_TTL_S), and an actively rotating client
        # outlives a registration record shorter than its refresh window.
        # max(90d, 3 × refresh TTL): the default keeps 90 days, a longer
        # refresh window scales the retention with it.
        self._registry_ttl_s = max(
            _CLIENT_REGISTRY_TTL_S, 3 * token_authority._refresh_ttl_s
        )

    def _default_audience(self) -> str:
        """Audience when the grant names no resource: the ticket-3
        ``resource_server_url`` when wired, else the same derivation
        the /mcp chain uses (``CANNBOT_MCP_PUBLIC_URL`` / localhost)."""
        return self._resource_server_url or (
            server.SelfIssuedTokenAuthority._default_audience(None)
        )

    def _register_refresh_jti(self, refresh: str) -> None:
        """Book a freshly minted refresh token's id for its whole
        lifetime, so the first refresh grant presenting it can consume
        it and a replay finds it gone (the handwritten token endpoint's
        ledger discipline)."""
        jti = server.SelfIssuedTokenAuthority.token_jti(refresh)
        assert jti is not None  # just signed: jti is always present
        self._token_store.put(
            f"jti:{jti}",
            "live",
            self._token_authority.refresh_remaining_s(refresh),
        )

    async def get_client(
        self, client_id: str
    ) -> OAuthClientInformationFull | None:
        cached = _clients.get(client_id)
        if cached is not None:
            info, expires_at = cached
            if expires_at > time.time():
                return info
            # Expired in the cache: the ledger is authoritative, so the
            # entry disappears from memory too (bounded cache, no
            # unbounded growth) and the lookup falls through to the
            # ledger below.
            del _clients[client_id]
        # Cache miss: a replica may have registered this client, or the
        # process restarted after the registration. Resolve from the
        # shared ledger before falling back to the public client.
        raw = self._token_store.get(_CLIENT_REGISTRY_PREFIX + client_id)
        if raw:
            try:
                info = OAuthClientInformationFull.model_validate_json(raw)
            except ValueError:
                return None
            # The ledger entry may be near its own expiry and StateStore.get
            # does not expose the remaining TTL, so cache the recovered
            # entry under a short window instead of a fresh full one: the
            # ledger stays authoritative even for replicas that recover an
            # old record, and a re-read costs one store get.
            _clients[client_id] = (info, time.time() + _CLIENT_RECOVERY_TTL_S)
            return info
        if client_id == PUBLIC_CLIENT_ID:
            return public_client_information()
        return None

    async def register_client(
        self, client_info: OAuthClientInformationFull
    ) -> None:
        # The SDK DCR handler generates a fresh random client_id, calls us
        # with the full info, and returns THAT id to the client — the token
        # exchange later resolves the same id via get_client. Storing only
        # the fixed public client here breaks that round-trip (token
        # exchange fails with "Existing OAuth client information is
        # required"). Register what the SDK minted, write it through to
        # the shared ledger (restarts and other replicas read it back),
        # and keep the fixed public client available through get_client's
        # fallback. The cache entry mirrors the ledger's TTL window so
        # memory never serves a registration the ledger has already
        # expired.
        expires_at = time.time() + self._registry_ttl_s
        _clients[client_info.client_id] = (client_info, expires_at)
        self._token_store.put(
            _CLIENT_REGISTRY_PREFIX + client_info.client_id,
            client_info.model_dump_json(exclude_none=True),
            self._registry_ttl_s,
        )

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        """Mint the one-shot authorization code and hand it back.

        The code, redirect_uri, code_challenge, state and resource are
        bound into the AuthCodeStore at mint (``create``), the identity
        is bound right away with the store's compare-and-swap ``bind``,
        and the returned URL is the client's redirect_uri with code and
        state appended — the same bounce the handwritten
        /oauth/authorize/confirm allow leg produces. The SDK authorize
        handler has already validated the client, the redirect_uri and
        the S256 challenge before calling this, so an empty challenge
        here is a tampered path and fails closed.
        """
        if not params.code_challenge:
            raise AuthorizeError(
                error="invalid_request",
                error_description="authorization request carries no PKCE code_challenge",
            )
        # RFC 8707: the client names the target service; trailing-slash
        # canonicalized exactly like the handwritten authorize endpoint.
        resource = (params.resource or "").strip().rstrip("/")
        session = self._auth_code_store.create(
            str(params.redirect_uri),
            params.code_challenge,
            params.state or "",
            resource,
        )
        bound = self._auth_code_store.bind(session.code, client.client_id)
        if bound is None:
            raise AuthorizeError(
                error="invalid_request",
                error_description="authorization code could not be bound; restart the flow",
            )
        return construct_redirect_uri(
            str(params.redirect_uri),
            code=session.code,
            state=params.state,
        )

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> CannbotAuthorizationCode | None:
        """Read the stored session back as an AuthorizationCode.

        None (the protocol's not-found signal; the SDK token handler
        turns it into invalid_grant) when the code is unknown, expired
        or already consumed. The session's fields map onto the model
        one-to-one; ``client_id`` is the binding authorize recorded —
        with the single fixed public client there is exactly one
        possible value, and the store schema has no client column to
        confuse it with.
        """
        raw = self._auth_code_store._store.get("ac:" + authorization_code)
        if raw is None:
            return None
        session = server.AuthCodeStore._session_from_value(raw)
        if session is None:
            return None
        return CannbotAuthorizationCode(
            code=session.code,
            scopes=["mcp"],
            expires_at=session.expires_at,
            client_id=client.client_id,
            code_challenge=session.code_challenge,
            redirect_uri=session.redirect_uri,
            redirect_uri_provided_explicitly=True,
            resource=session.resource or None,
            subject=session.username,
        )

    async def exchange_authorization_code(
        self,
        client: OAuthClientInformationFull,
        authorization_code: CannbotAuthorizationCode,
    ) -> OAuthToken:
        """One-shot code exchange: PKCE, bindings, then the token pair.

        The stored session is consumed atomically first (``take``), so
        a replay — racing or serial — finds nothing and gets
        invalid_grant; a failed validation after the take burns the
        code exactly like ``AuthCodeStore.consume``. PKCE: with a
        ``code_verifier`` on the presented object the full S256 digest
        runs here; without one the presented ``code_challenge`` must
        equal the authorize-time stored challenge (the SDK token
        handler already proved S256(verifier) against it). The minted
        pair is audience-bound to the grant's resource, or this
        server's resource URL when none was named.
        """
        raw = self._auth_code_store._store.take(
            "ac:" + authorization_code.code
        )
        session = (
            server.AuthCodeStore._session_from_value(raw)
            if raw is not None
            else None
        )
        if session is None:
            raise TokenError(
                error="invalid_grant",
                error_description="authorization code does not exist",
            )
        if session.expired:
            raise TokenError(
                error="invalid_grant",
                error_description="authorization code has expired",
            )
        if session.username is None:
            raise TokenError(
                error="invalid_grant",
                error_description="authorization code carries no bound identity",
            )
        # A missing challenge means a tampered/stale row, not a pre-PKCE
        # grant (authorize rejects those) — fail closed, like consume.
        if not session.code_challenge:
            raise TokenError(
                error="invalid_grant",
                error_description="authorization code carries no PKCE challenge",
            )
        if authorization_code.client_id != client.client_id:
            raise TokenError(
                error="invalid_grant",
                error_description="authorization code was issued to a different client",
            )
        if not server._loopback_redirect_match(
            session.redirect_uri, str(authorization_code.redirect_uri)
        ):
            raise TokenError(
                error="invalid_grant",
                error_description="redirect_uri does not match the authorize-time binding",
            )
        if authorization_code.code_verifier:
            if not hmac.compare_digest(
                _s256_digest(authorization_code.code_verifier),
                session.code_challenge,
            ):
                raise TokenError(
                    error="invalid_grant",
                    error_description="incorrect code_verifier",
                )
        elif not hmac.compare_digest(
            authorization_code.code_challenge, session.code_challenge
        ):
            raise TokenError(
                error="invalid_grant",
                error_description="code_challenge does not match the authorize-time binding",
            )
        audience = session.resource or self._default_audience()
        access, expires_in = self._token_authority.sign(
            session.username,
            server.SelfIssuedTokenAuthority._TYP_ACCESS,
            audience,
        )
        refresh, _ = self._token_authority.sign(
            session.username,
            server.SelfIssuedTokenAuthority._TYP_REFRESH,
            audience,
        )
        self._register_refresh_jti(refresh)
        return OAuthToken(
            access_token=access,
            refresh_token=refresh,
            expires_in=expires_in,
            token_type="Bearer",
        )

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        """Resolve a refresh token against the ledger.

        The JWT is verified locally (signature, refresh type, expiry —
        anchored on the token's own ``aud``, because the SDK handler
        drops the request's resource indicator and the handwritten flow
        keeps pairs on the audience they were minted for) and the jti
        must still be live in the one-time ledger. None (not-found,
        mapped to invalid_grant by the SDK handler) for anything else —
        an expired, tampered, access-typed or already-consumed token.
        """
        payload = _jwt_payload(refresh_token)
        aud = payload.get("aud")
        exp = payload.get("exp")
        audience = (
            aud if isinstance(aud, str) and aud else self._default_audience()
        )
        verified = self._token_authority.verify(
            refresh_token,
            server.SelfIssuedTokenAuthority._TYP_REFRESH,
            audience,
        )
        if verified is None:
            return None
        username, _typ = verified
        jti = server.SelfIssuedTokenAuthority.token_jti(refresh_token)
        if jti is None or self._token_store.get(f"jti:{jti}") != "live":
            return None  # unknown, or already consumed (one-shot ledger)
        return RefreshToken(
            token=refresh_token,
            client_id=client.client_id,
            scopes=["mcp"],
            expires_at=int(exp) if isinstance(exp, (int, float)) else None,
            resource=aud if isinstance(aud, str) and aud else None,
            subject=username,
        )

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        """Rotate the pair, one refresh presentation per token.

        The presented object is re-verified against its own claims
        (forged objects die on the signature or on the ledger), then the
        jti is consumed with the one-shot ``take_if_equal`` — a replay,
        racing or serial, finds the id gone and gets invalid_grant. The
        fresh pair keeps the SAME audience the old token carried
        (``refresh_token.resource``; the load path fills it from the
        token's own aud), which is the handwritten refresh grant's
        现状 semantics, and the new refresh id is booked into the ledger
        for its whole lifetime so the next rotation finds it.
        """
        if refresh_token.client_id != client.client_id:
            raise TokenError(
                error="invalid_grant",
                error_description="refresh token was issued to a different client",
            )
        audience = refresh_token.resource or self._default_audience()
        verified = self._token_authority.verify(
            refresh_token.token,
            server.SelfIssuedTokenAuthority._TYP_REFRESH,
            audience,
        )
        if verified is None:
            raise TokenError(
                error="invalid_grant",
                error_description="refresh token is invalid or expired",
            )
        username, _typ = verified
        jti = server.SelfIssuedTokenAuthority.token_jti(refresh_token.token)
        if jti is None or not self._token_store.take_if_equal(
            f"jti:{jti}", "live"
        ):
            raise TokenError(
                error="invalid_grant",
                error_description="refresh token is unknown or already used",
            )
        access, expires_in = self._token_authority.sign(
            username,
            server.SelfIssuedTokenAuthority._TYP_ACCESS,
            audience,
        )
        new_refresh, _ = self._token_authority.sign(
            username,
            server.SelfIssuedTokenAuthority._TYP_REFRESH,
            audience,
        )
        self._register_refresh_jti(new_refresh)
        return OAuthToken(
            access_token=access,
            refresh_token=new_refresh,
            expires_in=expires_in,
            token_type="Bearer",
        )

    # The remaining protocol surface belongs to later tickets; the
    # stubs below only mark what this ticket does not implement yet.
    async def exchange_identity_assertion(
        self, *args: object, **kwargs: object
    ):
        raise NotImplementedError("later ticket: exchange_identity_assertion")

    async def load_access_token(self, *args: object, **kwargs: object):
        raise NotImplementedError("later ticket: load_access_token")

    async def revoke_token(self, *args: object, **kwargs: object):
        raise NotImplementedError("later ticket: revoke_token")
