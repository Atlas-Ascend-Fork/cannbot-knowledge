# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / ".agents/skills/knowledge-query/scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from retrieval.index import (  # noqa: E402
        TOKENIZER_SUBWORD,
        TOKENIZER_V3,
        token_counts,
    )
except ImportError:
    pkg = sys.modules.setdefault("retrieval", types.ModuleType("retrieval"))
    pkg.__path__ = [str(SCRIPT_DIR / "retrieval")]
    stub = types.ModuleType("retrieval.root")
    stub.repository_state = lambda root: {}  # pragma: no cover
    stub.sha256_file = lambda path: ""  # pragma: no cover
    pkg.root = stub
    sys.modules["retrieval.root"] = stub
    from retrieval.index import (  # noqa: E402
        TOKENIZER_SUBWORD,
        TOKENIZER_V3,
        token_counts,
    )


class SubwordTokenizerTests(unittest.TestCase):
    def test_v3_keeps_underscore_names_whole(self) -> None:
        counts = token_counts("rms_norm_tiling", tokenizer=TOKENIZER_V3)
        self.assertEqual(1, counts["rms_norm_tiling"])
        self.assertNotIn("rms", counts)
        self.assertNotIn("norm", counts)

    def test_subword_splits_camel_and_underscores(self) -> None:
        counts = token_counts("DataCopyPad rms_norm", tokenizer=TOKENIZER_SUBWORD)
        self.assertGreaterEqual(counts["datacopypad"], 1)
        self.assertGreaterEqual(counts["copy"], 1)
        self.assertGreaterEqual(counts["pad"], 1)
        self.assertGreaterEqual(counts["rms_norm"], 1)
        self.assertGreaterEqual(counts["rms"], 1)
        self.assertGreaterEqual(counts["norm"], 1)

    def test_subword_does_not_double_count_unsplit_tokens(self) -> None:
        counts = token_counts("tensor", tokenizer=TOKENIZER_SUBWORD)
        self.assertEqual(1, counts["tensor"])

    def test_get_prefix_is_stripped_from_pieces_only(self) -> None:
        counts = token_counts("get_swi_glu_max_min", tokenizer=TOKENIZER_SUBWORD)
        self.assertGreaterEqual(counts["get_swi_glu_max_min"], 1)
        self.assertGreaterEqual(counts["swi"], 1)
        self.assertGreaterEqual(counts["glu"], 1)
        self.assertNotIn("get", counts)

    def test_getting_is_not_treated_as_an_accessor_prefix(self) -> None:
        counts = token_counts("getting started", tokenizer=TOKENIZER_SUBWORD)
        self.assertGreaterEqual(counts["getting"], 1)


if __name__ == "__main__":
    unittest.main()
