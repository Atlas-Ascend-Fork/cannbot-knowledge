"""Unit tests for the self-issued JWT authority."""
import os
import tempfile
import time
import unittest
from pathlib import Path

import server
import state_store


class SelfIssuedTokenAuthorityTests(unittest.TestCase):
    """Sign/verify round trips, expiry, type confusion, key rotation, TTL env."""

    def _authority(
        self, secret: str | None = "test-secret", env: dict | None = None
    ) -> server.SelfIssuedTokenAuthority:
        saved = {
            k: os.environ.get(k)
            for k in (
                server.AUTH_SECRET_ENV,
                server.ACCESS_TTL_ENV,
                server.REFRESH_TTL_ENV,
            )
        }
        try:
            os.environ[server.AUTH_SECRET_ENV] = secret or ""
            os.environ.pop(server.AUTH_SECRET_ENV, None) if secret is None else None
            for k, v in (env or {}).items():
                os.environ[k] = str(v)
            return server.SelfIssuedTokenAuthority()
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_sign_verify_roundtrip(self) -> None:
        a = self._authority()
        token, ttl = a.sign("demo-user", "access")
        self.assertEqual(ttl, 7 * 24 * 3600)
        self.assertEqual(("demo-user", "access"), a.verify(token))

    def test_refresh_token_roundtrip_and_ttls(self) -> None:
        a = self._authority(
            env={server.ACCESS_TTL_ENV: 3600, server.REFRESH_TTL_ENV: 7200}
        )
        _access, access_ttl = a.sign("u", "access")
        refresh, refresh_ttl = a.sign("u", "refresh")
        self.assertEqual(3600, access_ttl)
        self.assertEqual(7200, refresh_ttl)
        self.assertEqual(("u", "refresh"), a.verify(refresh, "refresh"))

    def test_type_confusion_rejected(self) -> None:
        a = self._authority()
        access, _ = a.sign("u", "access")
        self.assertIsNone(a.verify(access, "refresh"))
        refresh, _ = a.sign("u", "refresh")
        self.assertIsNone(a.verify(refresh, "access"))

    def test_expired_token_rejected(self) -> None:
        a = self._authority()
        token, _ = a.sign("u", "access")
        # Forge an expired sibling by signing with a tiny TTL env, then rewinding.
        b = self._authority(env={server.ACCESS_TTL_ENV: 1})
        short, _ = b.sign("u", "access")
        # Wait past expiry would slow tests; instead tamper iat/exp by hand is
        # blocked by the signature. So verify via a negative TTL path:
        c = self._authority(env={server.ACCESS_TTL_ENV: -10})
        expired, _ = c.sign("u", "access")
        self.assertIsNone(c.verify(expired))
        self.assertEqual(("u", "access"), a.verify(token))

    def test_key_rotation_invalidates_tokens(self) -> None:
        a = self._authority(secret="first-secret")
        token, _ = a.sign("u", "access")
        self.assertEqual(("u", "access"), a.verify(token))
        b = self._authority(secret="second-secret")
        self.assertIsNone(b.verify(token))

    def test_tampered_signature_rejected(self) -> None:
        a = self._authority()
        token, _ = a.sign("u", "access")
        head, body, _sig = token.split(".")
        forged = f"{head}.{body}.AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        self.assertIsNone(a.verify(forged))

    def test_malformed_tokens_rejected(self) -> None:
        a = self._authority()
        for bad in ("", "not-a-jwt", "a.b", "a.b.c.d", "///", "a.b.c"):
            with self.subTest(token=bad):
                self.assertIsNone(a.verify(bad))

    def test_env_secret_beats_generated_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            key_path = Path(tmp) / "auth.key"
            saved_path = server.DEFAULT_AUTH_KEY_PATH
            saved_secret = os.environ.get(server.AUTH_SECRET_ENV)
            try:
                server.DEFAULT_AUTH_KEY_PATH = key_path
                os.environ[server.AUTH_SECRET_ENV] = "explicit-secret"
                a = server.SelfIssuedTokenAuthority()
                self.assertEqual(b"explicit-secret", a._secret)
                self.assertFalse(key_path.exists())
            finally:
                server.DEFAULT_AUTH_KEY_PATH = saved_path
                if saved_secret is None:
                    os.environ.pop(server.AUTH_SECRET_ENV, None)
                else:
                    os.environ[server.AUTH_SECRET_ENV] = saved_secret

    def test_generated_key_persisted_with_0600(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            key_path = Path(tmp) / "nested" / "auth.key"
            saved_path = server.DEFAULT_AUTH_KEY_PATH
            saved_secret = os.environ.get(server.AUTH_SECRET_ENV)
            try:
                server.DEFAULT_AUTH_KEY_PATH = key_path
                os.environ.pop(server.AUTH_SECRET_ENV, None)
                a = server.SelfIssuedTokenAuthority()
                self.assertTrue(key_path.exists())
                self.assertEqual(0o600, key_path.stat().st_mode & 0o777)
                self.assertEqual(a._secret, key_path.read_bytes().strip())
                # A second instance with the same path reuses the same key.
                os.environ.pop(server.AUTH_SECRET_ENV, None)
                b = server.SelfIssuedTokenAuthority()
                self.assertEqual(a._secret, b._secret)
            finally:
                server.DEFAULT_AUTH_KEY_PATH = saved_path
                if saved_secret is None:
                    os.environ.pop(server.AUTH_SECRET_ENV, None)
                else:
                    os.environ[server.AUTH_SECRET_ENV] = saved_secret

    def test_unknown_token_type_raises(self) -> None:
        a = self._authority()
        with self.assertRaises(ValueError):
            a.sign("u", "session")


if __name__ == "__main__":
    unittest.main()
