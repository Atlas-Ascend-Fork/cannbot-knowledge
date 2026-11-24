"""CannbotTokenVerifier tests: the SDK TokenVerifier adapter's four-track
routing (ticket 2 of the SDK auth migration; wiring lands in a
later ticket, so these stay unit-level)."""
import asyncio
import base64
import json
import os
import tempfile
import unittest

import server
import sdk_auth_verifier
from mcp.server.auth.provider import AccessToken

PUBLIC_URL_ENV = "CANNBOT_MCP_PUBLIC_URL"


def _decode_payload(token: str) -> dict:
    body_b = token.split(".")[1]
    padding = "=" * (-len(body_b) % 4)
    return json.loads(base64.urlsafe_b64decode(body_b + padding))


class _RecordingGitCodeVerifier:
    """GitCode verifier stand-in recording every presented credential so
    tests can assert local tracks never leak outbound."""

    def __init__(self, result: AccessToken | None = None) -> None:
        self.result = result
        self.calls: list[str] = []

    async def verify_token(self, token: str) -> AccessToken | None:
        self.calls.append(token)
        return self.result


class CannbotTokenVerifierTests(unittest.TestCase):
    """verify_token maps each credential track onto the SDK protocol."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        env_keys = (server.AUTH_SECRET_ENV, server.ACCESS_TTL_ENV, PUBLIC_URL_ENV)
        self._saved = {k: os.environ.get(k) for k in env_keys}
        os.environ[server.AUTH_SECRET_ENV] = "test-secret"
        # Deterministic default audience: PUBLIC_URL unset ->
        # _default_audience(None) = http://localhost.
        os.environ.pop(PUBLIC_URL_ENV, None)
        self.authority = server.SelfIssuedTokenAuthority()
        self.gitcode = _RecordingGitCodeVerifier()
        self.verifier = sdk_auth_verifier.CannbotTokenVerifier(
            self.authority, self.gitcode
        )

    def tearDown(self) -> None:
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self._tmp.cleanup()

    def test_self_issued_access_jwt_maps_to_access_token(self) -> None:
        token, _ = self.authority.sign("device-user", "access")
        result = asyncio.run(self.verifier.verify_token(token))
        self.assertIsInstance(result, AccessToken)
        self.assertEqual("device-user", result.client_id)
        self.assertEqual("http://localhost", result.resource)  # resource = aud
        self.assertEqual(_decode_payload(token)["exp"], result.expires_at)
        self.assertEqual(token, result.token)
        # Local credential: never sent to GitCode.
        self.assertEqual([], self.gitcode.calls)

    def test_explicit_audience_binds_resource(self) -> None:
        token, _ = self.authority.sign(
            "device-user", "access", "https://svc.example.com"
        )
        result = asyncio.run(
            self.verifier.verify_token(token, audience="https://svc.example.com")
        )
        self.assertIsNotNone(result)
        self.assertEqual("https://svc.example.com", result.resource)
        # Audience mismatch is rejected (audience binding).
        self.assertIsNone(
            asyncio.run(
                self.verifier.verify_token(token, audience="https://other")
            )
        )

    def test_public_url_drives_default_audience(self) -> None:
        os.environ[PUBLIC_URL_ENV] = "https://public.example.com"
        token, _ = self.authority.sign("device-user", "access")
        result = asyncio.run(self.verifier.verify_token(token))
        self.assertIsNotNone(result)
        self.assertEqual("https://public.example.com", result.resource)

    def test_expired_jwt_rejected(self) -> None:
        os.environ[server.ACCESS_TTL_ENV] = "-5"
        try:
            expired_authority = server.SelfIssuedTokenAuthority()
            token, _ = expired_authority.sign("late-user", "access")
        finally:
            os.environ.pop(server.ACCESS_TTL_ENV, None)
        self.assertIsNone(asyncio.run(self.verifier.verify_token(token)))
        # Failed local verification never falls through to GitCode.
        self.assertEqual([], self.gitcode.calls)

    def test_tampered_jwt_rejected(self) -> None:
        token, _ = self.authority.sign("device-user", "access")
        head, body, sig = token.split(".")
        flipped = "AA" if not sig.endswith("AA") else "BB"
        tampered = f"{head}.{body}.{sig[:-2]}{flipped}"
        self.assertNotEqual(token, tampered)
        self.assertIsNone(asyncio.run(self.verifier.verify_token(tampered)))
        self.assertEqual([], self.gitcode.calls)

    def test_refresh_type_jwt_rejected(self) -> None:
        # Only access tokens are accepted; a refresh token is a local
        # credential, so it is rejected locally without a GitCode call.
        token, _ = self.authority.sign("device-user", "refresh")
        self.assertIsNone(asyncio.run(self.verifier.verify_token(token)))
        self.assertEqual([], self.gitcode.calls)

    def test_verifier_none_and_non_jwt_returns_none(self) -> None:
        verifier = sdk_auth_verifier.CannbotTokenVerifier(self.authority, None)
        self.assertIsNone(
            asyncio.run(verifier.verify_token("opaque-gitcode-pat"))
        )

    def test_opaque_token_uses_gitcode_track(self) -> None:
        expected = AccessToken(
            token="gc-opaque", client_id="gc-user", scopes=["mcp"]
        )
        self.gitcode.result = expected
        result = asyncio.run(self.verifier.verify_token("gc-opaque"))
        self.assertIs(expected, result)
        self.assertEqual(["gc-opaque"], self.gitcode.calls)

    def test_api_key_prefix_short_circuits(self) -> None:
        # The cbk_live_ API key track is split at the /mcp entry (ticket
        # 3), never verified here -- see the routing comment in the
        # adapter.
        self.assertIsNone(
            asyncio.run(self.verifier.verify_token("cbk_live_deadbeef"))
        )
        self.assertEqual([], self.gitcode.calls)


if __name__ == "__main__":
    unittest.main()
