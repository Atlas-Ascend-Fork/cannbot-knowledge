"""Unit tests for the self-service API key store."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

import api_keys


class ApiKeyStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "keys.db"
        self.store = api_keys.ApiKeyStore(self.path)

    def tearDown(self) -> None:
        self.store.close()
        self._tmp.cleanup()

    def test_create_and_verify_roundtrip(self) -> None:
        full, key_id = self.store.create("demo-user", "my-ci-runner")
        self.assertTrue(full.startswith(api_keys.ApiKeyStore._PREFIX))
        self.assertIn(key_id, full)
        self.assertEqual(
            ("demo-user", "my-ci-runner"), self.store.verify(full)
        )

    def test_secret_never_persisted(self) -> None:
        full, _ = self.store.create("demo-user", "my-ci")
        connection = sqlite3.connect(str(self.path))
        try:
            rows = list(connection.execute("SELECT * FROM api_keys"))
        finally:
            connection.close()
        blob = " ".join(str(row) for row in rows)
        # The secret is the final underscore-separated segment of the key;
        # also assert the WHOLE key body never appears (a truncated secret
        # could otherwise pass when the urlsafe tail is short).
        body = full.removeprefix(api_keys.ApiKeyStore._PREFIX)
        secret = body.rsplit("_", 1)[1]
        # Column-level check, immune to a one-character secret colliding
        # with an unrelated column (a 1-char urlsafe tail can occur by
        # chance in hash/salt text and would false-fail a blob scan).
        stored_secret_columns = (row[3] for row in rows)
        self.assertTrue(all(
            secret != column and body not in column
            for column in stored_secret_columns
        ))
        self.assertNotIn(body, blob)

    def test_tampered_secret_rejected(self) -> None:
        full, _ = self.store.create("demo-user", "my-ci")
        self.assertIsNone(self.store.verify(full[:-2] + "zz"))

    def test_unknown_prefix_rejected(self) -> None:
        self.assertIsNone(self.store.verify("cbk_other_k abc"))

    def test_revoke_then_verify_fails(self) -> None:
        full, key_id = self.store.create("demo-user", "my-ci")
        self.assertTrue(self.store.revoke(key_id, "demo-user"))
        self.assertIsNone(self.store.verify(full))

    def test_revoke_other_owners_key_fails(self) -> None:
        _, key_id = self.store.create("demo-user", "my-ci")
        self.assertFalse(self.store.revoke(key_id, "attacker"))

    def test_per_owner_limit(self) -> None:
        for i in range(10):
            self.assertIsNotNone(self.store.create("u", f"l{i}"))
        self.assertIsNone(self.store.create("u", "overflow"))

    def test_limit_is_per_owner(self) -> None:
        for i in range(10):
            self.store.create("u1", f"l{i}")
        # a second owner is unaffected
        self.assertIsNotNone(self.store.create("u2", "mine"))

    def test_revoked_slots_free_up(self) -> None:
        for i in range(10):
            _, key_id = self.store.create("u", f"l{i}")
        self.assertIsNone(self.store.create("u", "overflow"))
        self.store.revoke(key_id, "u")
        self.assertIsNotNone(self.store.create("u", "replacement"))

    def test_bad_labels_rejected(self) -> None:
        self.assertIsNone(self.store.create("u", ""))
        self.assertIsNone(self.store.create("u", "   "))
        self.assertIsNone(self.store.create("u", "x" * 33))

    def test_list_omits_secret_fields(self) -> None:
        self.store.create("demo-user", "my-ci")
        items = self.store.list("demo-user")
        self.assertEqual(1, len(items))
        self.assertEqual(
            {"key_id", "label", "created_at", "last_used"}, set(items[0])
        )

    def test_list_scoped_to_owner(self) -> None:
        self.store.create("alice", "a")
        self.store.create("bob", "b")
        self.assertEqual(1, len(self.store.list("alice")))

    def test_count_tracks_revocation(self) -> None:
        _, key_id = self.store.create("u", "a")
        self.assertEqual(1, self.store.count("u"))
        self.store.revoke(key_id, "u")
        self.assertEqual(0, self.store.count("u"))

    def test_verify_updates_last_used(self) -> None:
        full, _ = self.store.create("u", "a")
        self.store.verify(full)
        items = self.store.list("u")
        self.assertIsNotNone(items[0]["last_used"])


if __name__ == "__main__":
    unittest.main()
