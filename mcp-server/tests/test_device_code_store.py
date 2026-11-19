"""Unit tests for the device-code store."""
import os
import tempfile
import time
import unittest
from pathlib import Path

import server
import state_store


class DeviceCodeStoreTests(unittest.TestCase):
    """RFC 8628 session state machine, expiry, one-shot, persistence."""

    def _store(self, tmp: str, env: dict | None = None) -> server.DeviceCodeStore:
        saved = {k: os.environ.get(k) for k in (server.AUTH_DB_ENV, server.DEVICE_TTL_ENV)}
        try:
            os.environ[server.AUTH_DB_ENV] = str(Path(tmp) / "auth.db")
            for k, v in (env or {}).items():
                os.environ[k] = str(v)
            # 13c: the store is StateStore-backed; the shared backend
            # resolves beside the auth-db env path like before.
            backend = state_store.open_state_store()
            return server.DeviceCodeStore(backend)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_create_lookup_allow_poll_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            device_code, user_code = store.create()
            self.assertEqual(9, len(user_code))  # XXXX-XXXX
            self.assertEqual("-", user_code[4])
            session = store.lookup(user_code)
            self.assertIsNotNone(session)
            self.assertEqual("pending", session.state)
            allowed = store.allow(user_code, "demo-user")
            self.assertIsNotNone(allowed)
            self.assertEqual("allowed", allowed.state)
            self.assertEqual("demo-user", allowed.username)
            polled = store.poll(device_code)
            self.assertEqual(("allowed", "demo-user"), (polled.state, polled.username))
            store.close()

    def test_deny_is_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            device_code, user_code = store.create()
            denied = store.deny(user_code)
            self.assertEqual("denied", denied.state)
            # Terminal: no state change after the verdict.
            self.assertIsNone(store.allow(user_code, "someone"))
            self.assertIsNone(store.lookup(user_code))
            polled = store.poll(device_code)
            self.assertEqual("denied", polled.state)
            store.close()

    def test_allowed_is_one_shot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            _device, user_code = store.create()
            self.assertIsNotNone(store.allow(user_code, "u1"))
            # Second allow and lookup both refuse; poll still reports terminal state.
            self.assertIsNone(store.allow(user_code, "u2"))
            self.assertIsNone(store.lookup(user_code))
            store.close()

    def test_expiry_rejects_both_legs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp, {server.DEVICE_TTL_ENV: 1})
            device_code, user_code = store.create()
            time.sleep(1.1)
            self.assertIsNone(store.lookup(user_code))
            self.assertIsNone(store.allow(user_code, "u"))
            self.assertIsNone(store.deny(user_code))
            self.assertIsNone(store.poll(device_code))
            store.close()

    def test_unknown_codes_return_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            self.assertIsNone(store.lookup("ZZZZ-ZZZZ"))
            self.assertIsNone(store.allow("ZZZZ-ZZZZ", "u"))
            self.assertIsNone(store.poll("no-such-device-code"))
            store.close()

    def test_ttl_env_respected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp, {server.DEVICE_TTL_ENV: 120})
            self.assertEqual(120, store.ttl_s)
            store.close()

    def test_persistence_across_instances(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "auth.db")
            saved = os.environ.get(server.AUTH_DB_ENV)
            os.environ[server.AUTH_DB_ENV] = db
            try:
                first = server.DeviceCodeStore(state_store.open_state_store())
                device_code, user_code = first.create()
                first.allow(user_code, "persisted-user")
                first.close()
                # A second instance on the SAME backend sees the session —
                # the multi-node sharing proof at the unit level.
                second = server.DeviceCodeStore(state_store.open_state_store())
                polled = second.poll(device_code)
                self.assertEqual("persisted-user", polled.username)
                second.close()
            finally:
                if saved is None:
                    os.environ.pop(server.AUTH_DB_ENV, None)
                else:
                    os.environ[server.AUTH_DB_ENV] = saved

    def test_user_code_format_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            for _ in range(20):
                _device, user_code = store.create()
                prefix, suffix = user_code.split("-")
                self.assertEqual(4, len(prefix))
                self.assertEqual(4, len(suffix))
                for ch in prefix + suffix:
                    self.assertIn(ch, server.DeviceCodeStore._ALPHABET)
            store.close()


if __name__ == "__main__":
    unittest.main()
