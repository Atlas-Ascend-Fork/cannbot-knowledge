"""Startup auth-track enforcement tests.

main() must refuse HTTP startup only when ALL auth tracks are off:
empty static list AND GitCode verify off AND self-hosted AS off. Any one
live track keeps the service startable; an empty static list alone now
prints guidance about self-service API keys and continues.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import server
import state_store


class StartupAuthTrackTests(unittest.TestCase):
    """Drive main() with --transport http and inspect the exit path."""

    def _run_main(self) -> int:
        # Bypass uvicorn: build_http_app succeeds then uvicorn.run is a
        # mock, so the function returns 0 without serving.
        with mock.patch("uvicorn.run"):
            return server.main(["--transport", "http"])

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        saved = {
            name: os.environ.get(name)
            for name in (
                server.TOKENS_ENV,
                server.GITCODE_VERIFY_ENV,
                server.AUTH_SERVER_ENV,
                server.AUTH_DB_ENV,
                server.AUTH_SECRET_ENV,
                server.ENGINE_ENV,
                "CANNBOT_MCP_LOG",
            )
        }
        self._saved = saved
        # Neutral defaults: no tokens, both dynamic tracks on. These tests
        # are about auth tracks, not the retrieval engine: pin the subprocess
        # adapter so startup stays cheap instead of prewarming the resident
        # engine against the real repository index.
        os.environ.pop(server.TOKENS_ENV, None)
        os.environ.pop(server.GITCODE_VERIFY_ENV, None)
        os.environ.pop(server.AUTH_SERVER_ENV, None)
        os.environ[server.ENGINE_ENV] = "subprocess"
        os.environ[server.AUTH_DB_ENV] = str(Path(self._tmp.name) / "auth.db")
        os.environ[server.AUTH_SECRET_ENV] = "test-secret"
        os.environ["CANNBOT_MCP_LOG"] = "off"

    def tearDown(self) -> None:
        for name, value in self._saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        self._tmp.cleanup()

    def test_empty_tokens_with_tracks_on_starts(self) -> None:
        # 12b: empty static list + default tracks → info line, start OK.
        exit_code = self._run_main()
        self.assertEqual(0, exit_code)

    def test_all_tracks_off_refuses_startup(self) -> None:
        os.environ[server.GITCODE_VERIFY_ENV] = "off"
        os.environ[server.AUTH_SERVER_ENV] = "off"
        with mock.patch("sys.stderr", new=sys.stderr):
            exit_code = self._run_main()
        self.assertEqual(2, exit_code)

    def test_static_tokens_rescue_off_tracks(self) -> None:
        os.environ[server.GITCODE_VERIFY_ENV] = "off"
        os.environ[server.AUTH_SERVER_ENV] = "off"
        os.environ[server.TOKENS_ENV] = "cbk_x:label"
        self.assertEqual(0, self._run_main())

    def test_gitcode_track_rescues_off_as(self) -> None:
        os.environ[server.AUTH_SERVER_ENV] = "off"
        self.assertEqual(0, self._run_main())

    def test_as_track_rescues_off_gitcode(self) -> None:
        os.environ[server.GITCODE_VERIFY_ENV] = "off"
        self.assertEqual(0, self._run_main())


if __name__ == "__main__":
    unittest.main()
