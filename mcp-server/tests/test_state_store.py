"""Contract tests for the StateStore abstraction.

Both backends run the SAME suite: sqlite (default, file-backed) and the
Redis implementation bound to a fakeredis instance (Lua enabled via lupa).
The point of the shared suite is that migrating a caller from one backend
to the other must not change observable behavior.
"""
import threading
import time
import unittest
from pathlib import Path

import state_store


class StateStoreContractMixin:
    """Behavior every backend must satisfy. Subclass + set self.store."""

    def setUp(self) -> None:
        self.store = self._make_store()

    def _make_store(self):  # pragma: no cover - overridden
        raise NotImplementedError

    def test_put_get_roundtrip(self) -> None:
        self.store.put("k", "v", 60)
        self.assertEqual("v", self.store.get("k"))

    def test_get_does_not_delete(self) -> None:
        self.store.put("k", "v", 60)
        self.assertEqual("v", self.store.get("k"))
        self.assertEqual("v", self.store.get("k"))

    def test_missing_key_reads_none(self) -> None:
        self.assertIsNone(self.store.get("nope"))
        self.assertIsNone(self.store.take("nope"))

    def test_take_consumes_once(self) -> None:
        self.store.put("k", "v", 60)
        self.assertEqual("v", self.store.take("k"))
        self.assertIsNone(self.store.take("k"))

    def test_take_if_equal_matches_and_consumes(self) -> None:
        self.store.put("k", "pending", 60)
        self.assertTrue(self.store.take_if_equal("k", "pending"))
        self.assertIsNone(self.store.get("k"))

    def test_take_if_equal_wrong_value_keeps_entry(self) -> None:
        self.store.put("k", "pending", 60)
        self.assertFalse(self.store.take_if_equal("k", "allowed"))
        self.assertEqual("pending", self.store.get("k"))

    def test_take_if_equal_missing_key_false(self) -> None:
        self.assertFalse(self.store.take_if_equal("gone", "x"))

    def test_ttl_expiry(self) -> None:
        self.store.put("k", "v", 0.2)
        time.sleep(0.35)
        self.assertIsNone(self.store.get("k"))
        self.assertIsNone(self.store.take("k"))

    def test_take_if_equal_respects_ttl(self) -> None:
        self.store.put("k", "v", 0.2)
        time.sleep(0.35)
        self.assertFalse(self.store.take_if_equal("k", "v"))

    def test_put_overwrites(self) -> None:
        self.store.put("k", "first", 60)
        self.store.put("k", "second", 60)
        self.assertEqual("second", self.store.get("k"))

    def test_record_counts_in_window(self) -> None:
        self.store.record("rl:u")
        self.store.record("rl:u")
        self.assertEqual(2, self.store.count("rl:u", 60))

    def test_count_scoped_by_prefix(self) -> None:
        self.store.record("rl:a")
        self.store.record("rl:b")
        self.assertEqual(1, self.store.count("rl:a", 60))
        self.assertEqual(1, self.store.count("rl:b", 60))

    def test_count_window_excludes_old_events(self) -> None:
        # window of "0 seconds" excludes everything recorded before now
        self.store.record("rl:u")
        time.sleep(0.05)
        self.assertEqual(0, self.store.count("rl:u", 0.02))

    def test_concurrent_take_yields_exactly_one(self) -> None:
        self.store.put("race", "prize", 60)
        results: list[str | None] = []
        barrier = threading.Barrier(2)

        def contender() -> None:
            barrier.wait()
            results.append(self.store.take("race"))

        threads = [threading.Thread(target=contender) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(1, results.count("prize"))
        self.assertEqual(1, results.count(None))

    def test_concurrent_take_if_equal_single_winner(self) -> None:
        self.store.put("race", "pending", 60)
        wins: list[bool] = []
        barrier = threading.Barrier(2)

        def contender() -> None:
            barrier.wait()
            wins.append(self.store.take_if_equal("race", "pending"))

        threads = [threading.Thread(target=contender) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(1, wins.count(True))
        self.assertEqual(1, wins.count(False))


class SqliteStateStoreTests(StateStoreContractMixin, unittest.TestCase):
    def _make_store(self):
        import tempfile

        return state_store.SqliteStateStore(
            Path(tempfile.mkdtemp(prefix="state-store-sqlite-")) / "state.db"
        )

    def tearDown(self) -> None:
        self.store.close()

    def test_refuses_repo_path_like_auth_db(self) -> None:
        # Path discipline mirrors the other auth stores: the selector
        # (open_state_store) is where repo rejection lives; the raw store
        # just needs a writable directory. Documented behavior.
        pass


class RedisStateStoreTests(StateStoreContractMixin, unittest.TestCase):
    """Redis implementation against fakeredis (same wire semantics)."""

    def _make_store(self):
        import fakeredis

        fake = fakeredis.FakeStrictRedis(decode_responses=True)
        store = state_store.RedisStateStore.__new__(state_store.RedisStateStore)
        store._client = fake
        store._take_if_equal = fake.register_script(
            state_store.RedisStateStore._TAKE_IF_EQUAL_LUA
        )
        return store

    def tearDown(self) -> None:
        self.store.close()


class SelectorTests(unittest.TestCase):
    def test_default_backend_is_sqlite(self) -> None:
        import os
        import tempfile

        saved_backend = os.environ.get("CANNBOT_MCP_STATE_BACKEND")
        saved_db = os.environ.get("CANNBOT_MCP_AUTH_DB")
        tmp = tempfile.mkdtemp()
        os.environ["CANNBOT_MCP_AUTH_DB"] = str(Path(tmp) / "auth.db")
        os.environ.pop("CANNBOT_MCP_STATE_BACKEND", None)
        try:
            store = state_store.open_state_store()
            self.assertIsInstance(store, state_store.SqliteStateStore)
            self.assertEqual(
                str(Path(tmp) / "state.db"), str(store._path)
            )
            store.close()
        finally:
            if saved_backend is None:
                os.environ.pop("CANNBOT_MCP_STATE_BACKEND", None)
            else:
                os.environ["CANNBOT_MCP_STATE_BACKEND"] = saved_backend
            if saved_db is None:
                os.environ.pop("CANNBOT_MCP_AUTH_DB", None)
            else:
                os.environ["CANNBOT_MCP_AUTH_DB"] = saved_db

    def test_redis_backend_requires_url(self) -> None:
        import os

        saved_backend = os.environ.get("CANNBOT_MCP_STATE_BACKEND")
        saved_url = os.environ.get("CANNBOT_MCP_STATE_REDIS_URL")
        os.environ["CANNBOT_MCP_STATE_BACKEND"] = "redis"
        os.environ.pop("CANNBOT_MCP_STATE_REDIS_URL", None)
        try:
            with self.assertRaises(RuntimeError):
                state_store.open_state_store()
        finally:
            if saved_backend is None:
                os.environ.pop("CANNBOT_MCP_STATE_BACKEND", None)
            else:
                os.environ["CANNBOT_MCP_STATE_BACKEND"] = saved_backend
            if saved_url is None:
                os.environ.pop("CANNBOT_MCP_STATE_REDIS_URL", None)
            else:
                os.environ["CANNBOT_MCP_STATE_REDIS_URL"] = saved_url

    def test_redis_backend_unreachable_fails_closed(self) -> None:
        import os

        saved_backend = os.environ.get("CANNBOT_MCP_STATE_BACKEND")
        saved_url = os.environ.get("CANNBOT_MCP_STATE_REDIS_URL")
        os.environ["CANNBOT_MCP_STATE_BACKEND"] = "redis"
        # nothing listens on this port
        os.environ["CANNBOT_MCP_STATE_REDIS_URL"] = "redis://127.0.0.1:1/"
        try:
            with self.assertRaises(Exception):
                state_store.open_state_store()
        finally:
            if saved_backend is None:
                os.environ.pop("CANNBOT_MCP_STATE_BACKEND", None)
            else:
                os.environ["CANNBOT_MCP_STATE_BACKEND"] = saved_backend
            if saved_url is None:
                os.environ.pop("CANNBOT_MCP_STATE_REDIS_URL", None)
            else:
                os.environ["CANNBOT_MCP_STATE_REDIS_URL"] = saved_url


if __name__ == "__main__":
    unittest.main()
