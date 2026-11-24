# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software: you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT OF MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""SDK TokenVerifier adapter bridging the official MCP SDK auth stack onto
the existing four-track credential verification (ticket 2 of
the SDK wiring ticket mounts it behind the
CANNBOT_MCP_SDK_AUTH env switch on the MCPServer constructor).
"""

from __future__ import annotations

import binascii
import json

from mcp.server.auth.provider import AccessToken

import server


class CannbotTokenVerifier:
    """``mcp.server.auth.provider.TokenVerifier`` over the existing tracks.

    The SDK's bearer middleware calls ``verify_token(token)``; the routing
    below mirrors the /mcp chain in ``server.build_http_app``:

    - ``cbk_live_`` API keys return None: that track is verified by the
      scrypt check in ``api_keys.ApiKeyStore`` and ticket 3 splits it out
      at the /mcp entry before this adapter sees the credential. Returning
      None here is not a verdict -- the API key leg never consults this
      adapter.
    - Self-issued JWTs (payload ``typ`` marker, per
      ``server._is_self_issued_jwt``) are verified locally only and never
      sent to GitCode; a failed local check (expired, tampered or
      refresh-type) does not fall through to the GitCode track, or a
      cross-track fallback would leak a local credential in an outbound
      Authorization header. Foreign JWT-shaped tokens (GitCode OAuth
      access tokens) lack the marker and still take the GitCode track.
    - Everything else (opaque GitCode OAuth/PAT tokens) goes to the
      GitCode verifier; ``gitcode_verifier`` None disables the track.

    ``resource_server_url`` (ticket 3 wiring, RFC 8707): the canonical
    resource identity the SDK stack serves under. When given it becomes
    the default audience for the self-issued track (``aud`` must equal the
    FULL endpoint URL, per the full-endpoint resource identity) and the
    declared ``AccessToken.resource`` for the GitCode track (the SDK's
    ``BearerAuthBackend`` with ``validate_token_resource=True`` compares
    it exactly, and GitCode tokens carry no resource indicator of their
    own). When None the audience derivation keeps the ticket-2 behaviour
    (``SelfIssuedTokenAuthority._default_audience(None)``).
    """

    def __init__(
        self,
        token_authority: server.SelfIssuedTokenAuthority,
        gitcode_verifier: server.GitCodeTokenVerifier | None = None,
        resource_server_url: str | None = None,
    ) -> None:
        self._token_authority = token_authority
        self._gitcode_verifier = gitcode_verifier
        self._resource_server_url = resource_server_url

    @staticmethod
    def _jwt_payload(token: str) -> dict[str, object]:
        """Read ``exp``/``aud`` from the payload of an ALREADY locally
        verified token -- the signature check happened in
        ``token_authority.verify`` right before, so this only extracts
        claims, it never authenticates."""
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

    async def verify_token(
        self, token: str, audience: str | None = None
    ) -> AccessToken | None:
        # ``audience`` defaults to this service's canonical resource URL:
        # ``resource_server_url`` when the ticket-3 wiring provided it (the
        # SDK's BearerAuthBackend calls verify_token without an audience),
        # else ``SelfIssuedTokenAuthority._default_audience(None)`` which
        # reads CANNBOT_MCP_PUBLIC_URL (falling back to http://localhost)
        # -- the same derivation the /mcp chain uses for its audience
        # binding.
        if token.startswith("cbk_live_"):
            # API key track: not this adapter's scope. Ticket 3 routes
            # ``cbk_live_`` credentials to the ApiKeyStore scrypt check at
            # the /mcp entry, split off before the SDK middleware sees
            # them; a key reaching this adapter is by construction
            # unroutable here.
            return None
        if server._is_self_issued_jwt(token):
            resolved_audience = audience or (
                self._resource_server_url
                or server.SelfIssuedTokenAuthority._default_audience(None)
            )
            identity = self._token_authority.verify(
                token,
                server.SelfIssuedTokenAuthority._TYP_ACCESS,
                resolved_audience,
            )
            if identity is None:
                return None
            subject = identity[0]
            payload = self._jwt_payload(token)
            exp = payload.get("exp")
            aud = payload.get("aud")
            return AccessToken(
                token=token,
                client_id=subject,
                scopes=["mcp"],
                expires_at=(
                    int(exp) if isinstance(exp, (int, float)) else None
                ),
                resource=(
                    aud if isinstance(aud, str) and aud else resolved_audience
                ),
                subject=subject,
            )
        if self._gitcode_verifier is None:
            return None
        verified = await self._gitcode_verifier.verify_token(token)
        if verified is None or not self._resource_server_url:
            return verified
        # RFC 8707 declaration for the SDK stack: GitCode tokens carry no
        # resource indicator, so acceptance of THIS service is declared
        # here (per the audience mapping -- the mapping does
        # not widen any permission; the token already verified against the
        # GitCode user API).
        return AccessToken(
            token=verified.token,
            client_id=verified.client_id,
            scopes=list(verified.scopes),
            expires_at=verified.expires_at,
            resource=self._resource_server_url,
            subject=verified.subject,
        )
