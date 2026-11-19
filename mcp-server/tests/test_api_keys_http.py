"""ASGI-level tests for /api/keys and the /mcp fourth track."""
import asyncio
import json
import os
import tempfile
import unittest
import urllib.parse
from pathlib import Path

import server
import state_store


def _form(fields: dict) -> bytes:
    return urllib.parse.urlencode(fields).encode()


def _json_headers(bearer: str | None) -> list[tuple[bytes, bytes]]:
    headers = [(b"content-type", b"application/json")]
    if bearer:
        headers.append((b"authorization", f"Bearer {bearer}".encode()))
    return headers


class ApiKeysHttpTests(unittest.TestCase):
    def _app(self) -> object:
        async def stub_inner(scope, receive, send) -> None:
            raise AssertionError("api-keys endpoints must not reach the MCP app")

        class StubMcpServer:
            def streamable_http_app(self, **_kwargs: object) -> object:
                return stub_inner

        return server.build_http_app(
            StubMcpServer(),
            server.TokenList.parse("cbk_ready:ready"),
            server.SlidingWindowRateLimiter(state_store.open_state_store()),
            server.IpCooldown(state_store.open_state_store()),
            0,
            "127.0.0.1",
        )

    def _request(
        self,
        app: object,
        path: str,
        method: str = "POST",
        body: bytes = b"",
        bearer: str | None = None,
        query: bytes = b"",
        statuses: tuple = (200, 400, 401, 404, 405),
    ) -> tuple[dict | None, int]:
        sent: list[dict] = []

        async def receive() -> dict:
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message: dict) -> None:
            sent.append(message)

        scope = {
            "type": "http",
            "method": method,
            "path": path.split("?")[0] if path.startswith("/") else path,
            "query_string": query,
            "headers": _json_headers(bearer),
            "client": ("10.8.8.8", 44444),
        }
        asyncio.run(app(scope, receive, send))
        status = sent[0]["status"] if sent else None
        payload = b"".join(
            m.get("body", b"") for m in sent if m["type"] == "http.response.body"
        )
        assert status in statuses, (status, payload[:200])
        try:
            parsed = json.loads(payload)
        except ValueError:
            parsed = None
        return parsed, status

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        saved_db = os.environ.get(server.AUTH_DB_ENV)
        saved_secret = os.environ.get(server.AUTH_SECRET_ENV)
        os.environ[server.AUTH_DB_ENV] = str(Path(self._tmp.name) / "auth.db")
        os.environ[server.AUTH_SECRET_ENV] = "test-secret"
        self._saved = (saved_db, saved_secret)
        self.app = self._app()
        self.authority = server.SelfIssuedTokenAuthority()
        self.access, _ = self.authority.sign("demo-user", "access")
        self.refresh, _ = self.authority.sign("demo-user", "refresh")

    def tearDown(self) -> None:
        saved_db, saved_secret = self._saved
        if saved_db is None:
            os.environ.pop(server.AUTH_DB_ENV, None)
        else:
            os.environ[server.AUTH_DB_ENV] = saved_db
        if saved_secret is None:
            os.environ.pop(server.AUTH_SECRET_ENV, None)
        else:
            os.environ[server.AUTH_SECRET_ENV] = saved_secret
        self._tmp.cleanup()

    def test_full_lifecycle(self) -> None:
        # create
        payload, status = self._request(
            self.app,
            "/api/keys",
            method="POST",
            body=_form({"label": "my-ci"}),
            bearer=self.access,
        )
        self.assertEqual(200, status)
        full_key = payload["key"]
        self.assertTrue(full_key.startswith("cbk_live_"))
        key_id = payload["key_id"]
        # list: no plaintext, no hash fields
        payload, _ = self._request(
            self.app, "/api/keys", method="GET", bearer=self.access
        )
        self.assertEqual(1, len(payload["keys"]))
        entry = payload["keys"][0]
        self.assertEqual(key_id, entry["key_id"])
        self.assertEqual("my-ci", entry["label"])
        self.assertNotIn("key", entry)
        self.assertNotIn("key_hash", entry)
        self.assertNotIn("salt", entry)
        # the created key opens /mcp's fourth track via the auth chain:
        # a wrong bearer (the api key itself) is rejected by /api/keys...
        payload, status = self._request(
            self.app, "/api/keys", method="GET", bearer=full_key
        )
        self.assertEqual(401, status)
        # ...and accepted by /mcp with principal owner/label (checked at the
        # store level below to avoid driving the full MCP handshake here).
        import api_keys as api_keys_module

        store = api_keys_module.ApiKeyStore(
            Path(self._tmp.name) / "apikeys.db"
        )
        self.assertEqual(
            ("demo-user", "my-ci"), store.verify(full_key)
        )
        store.close()
        # revoke
        query = urllib.parse.urlencode({"key_id": key_id}).encode()
        payload, status = self._request(
            self.app,
            "/api/keys",
            method="DELETE",
            bearer=self.access,
            query=query,
        )
        self.assertEqual(200, status)
        # after revoke: key dead, list empty
        store2 = api_keys_module.ApiKeyStore(
            Path(self._tmp.name) / "apikeys.db"
        )
        self.assertIsNone(store2.verify(full_key))
        store2.close()
        payload, _ = self._request(
            self.app, "/api/keys", method="GET", bearer=self.access
        )
        self.assertEqual(0, len(payload["keys"]))

    def test_no_jwt_rejected(self) -> None:
        _, status = self._request(self.app, "/api/keys", method="GET")
        self.assertEqual(401, status)

    def test_refresh_jwt_rejected(self) -> None:
        _, status = self._request(
            self.app, "/api/keys", method="GET", bearer=self.refresh
        )
        self.assertEqual(401, status)

    def test_cross_user_delete_404(self) -> None:
        other_access, _ = self.authority.sign("attacker", "access")
        payload, _ = self._request(
            self.app,
            "/api/keys",
            method="POST",
            body=_form({"label": "mine"}),
            bearer=self.access,
        )
        key_id = payload["key_id"]
        query = urllib.parse.urlencode({"key_id": key_id}).encode()
        _, status = self._request(
            self.app,
            "/api/keys",
            method="DELETE",
            bearer=other_access,
            query=query,
        )
        self.assertEqual(404, status)
        # owner can still see and delete it
        payload, _ = self._request(
            self.app, "/api/keys", method="GET", bearer=self.access
        )
        self.assertEqual(1, len(payload["keys"]))
        _, status = self._request(
            self.app,
            "/api/keys",
            method="DELETE",
            bearer=self.access,
            query=query,
        )
        self.assertEqual(200, status)

    def test_bad_label_400(self) -> None:
        _, status = self._request(
            self.app,
            "/api/keys",
            method="POST",
            body=_form({"label": ""}),
            bearer=self.access,
        )
        self.assertEqual(400, status)

    def test_delete_without_key_id_400(self) -> None:
        _, status = self._request(
            self.app, "/api/keys", method="DELETE", bearer=self.access
        )
        self.assertEqual(400, status)

    def test_method_not_allowed(self) -> None:
        _, status = self._request(
            self.app, "/api/keys", method="PUT", bearer=self.access
        )
        self.assertEqual(405, status)


if __name__ == "__main__":
    unittest.main()
