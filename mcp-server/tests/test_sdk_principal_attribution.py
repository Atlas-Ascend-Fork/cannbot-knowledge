# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software: you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Principal attribution in the SDK auth mode call log.

The SDK-mode /mcp wrapper sets request_meta BEFORE the SDK middleware
verifies the credential (the verdict lands one layer deeper, inside
`inner`), so meta.principal is None there and the call log loses the
caller identity. The fix is a read-side fallback in _logged_call: when
meta.principal is None, read the SDK's auth contextvar
(get_access_token()) — the AuthContextMiddleware publishes the
authenticated user in the same task context the tool call runs in, so
the subject is reachable at log time without touching the wrapper or
the SDK middleware stack.

These tests drive _logged_call directly (the unit under test is the
fallback, not the transport) with both contextvars set the way the two
layers set them at runtime, plus the off-mode regression: a
meta.principal from the handwritten chain is never overridden by the
SDK fallback.
"""
import unittest

from mcp.server.auth.middleware.auth_context import auth_context_var
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken

import server


class _RecordingLogger:
    """Capture log_call kwargs instead of writing JSONL."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def log_call(self, **kwargs) -> None:
        self.calls.append(kwargs)


def _access_token(subject: str | None) -> AccessToken:
    return AccessToken(
        token="probe-token",
        client_id="probe-client",
        scopes=["mcp"],
        subject=subject,
    )


class PrincipalFallbackTests(unittest.TestCase):
    """_logged_call resolves the principal from the SDK contextvar."""

    def setUp(self) -> None:
        self._saved_logger = server._LOGGER
        self.logger = _RecordingLogger()
        server._LOGGER = self.logger
        self._token = auth_context_var.set(None)
        self._meta = server.request_meta.set(
            server.RequestMeta(transport="http", principal=None, jsonrpc_id=7)
        )
        self.addCleanup(self._restore)

    def _restore(self) -> None:
        server._LOGGER = self._saved_logger
        auth_context_var.reset(self._token)
        server.request_meta.reset(self._meta)

    def _run_logged_call(self) -> None:
        import asyncio

        async def action() -> dict:
            return {"request_sha256": "abc", "cards": 3}

        asyncio.run(server._logged_call("discover", {}, action))

    def test_sdk_subject_used_when_meta_principal_is_none(self) -> None:
        # The SDK mode shape: wrapper set principal=None, the SDK
        # middleware verified "zhangsan" and published it on its own
        # contextvar.
        auth_context_var.set(AuthenticatedUser(_access_token("zhangsan")))
        self._run_logged_call()
        self.assertEqual(1, len(self.logger.calls))
        self.assertEqual("zhangsan", self.logger.calls[0]["principal"])

    def test_anonymous_stays_none_without_sdk_user(self) -> None:
        # No credential anywhere (stdio default, or an unauthenticated
        # path): the fallback must not invent a principal.
        self._run_logged_call()
        self.assertEqual(1, len(self.logger.calls))
        self.assertIsNone(self.logger.calls[0]["principal"])

    def test_meta_principal_is_never_overridden(self) -> None:
        # The handwritten chain's own attribution (SDK_AUTH=off mode,
        # static-token principal "ops/label" style) wins over the SDK
        # fallback: the bridge only fills the None gap.
        server.request_meta.set(
            server.RequestMeta(transport="http", principal="runner-1", jsonrpc_id=7)
        )
        auth_context_var.set(AuthenticatedUser(_access_token("zhangsan")))
        self._run_logged_call()
        self.assertEqual("runner-1", self.logger.calls[0]["principal"])

    def test_token_without_subject_stays_anonymous(self) -> None:
        # An AccessToken with a null subject (a foreign client-credential
        # shape) must not leak client_id or an empty string as principal.
        auth_context_var.set(AuthenticatedUser(_access_token(None)))
        self._run_logged_call()
        self.assertIsNone(self.logger.calls[0]["principal"])


if __name__ == "__main__":
    unittest.main()
