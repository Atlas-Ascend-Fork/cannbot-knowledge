# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Triton interpreter 数值用例的轻量入口。

torch/triton 是可选依赖：缺失时本模块只做 import 与依赖探测，测试通过
unittest.SkipTest 跳过，保证 `python3 -m unittest discover -s evals` 在默认的
轻量环境仍能完成收集。解释器用例在 evals/triton_skeleton_numerics_runner.py 的
独立子进程中执行，TRITON_INTERPRET=1 只作用于该子进程。
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPOSITORY_ROOT / "evals/triton_skeleton_numerics_runner.py"
OPTIONAL_DEPENDENCIES = ("torch", "triton")
DEPENDENCY_MISSING_EXIT = 77


def _missing_dependencies() -> list[str]:
    missing = []
    for name in OPTIONAL_DEPENDENCIES:
        try:
            spec = importlib.util.find_spec(name)
        except (ImportError, ValueError):
            spec = None
        if spec is None:
            missing.append(name)
    return missing


class TritonSkeletonNumericsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        missing = _missing_dependencies()
        if missing:
            raise unittest.SkipTest(
                "optional dependencies unavailable: " + ", ".join(missing)
            )

    def _run_interpreter_class(self, class_name: str) -> None:
        # 每个 class 都在独立进程中运行：interpreter 模式必须在 import triton
        # 之前设置，不能在导入本模块时修改整个测试进程的环境。
        env = os.environ.copy()
        env["TRITON_INTERPRET"] = "1"
        completed = subprocess.run(
            [sys.executable, str(RUNNER), "--class", class_name],
            cwd=REPOSITORY_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        output = (completed.stdout or "") + (completed.stderr or "")
        if completed.returncode == DEPENDENCY_MISSING_EXIT:
            self.skipTest(output.strip() or "interpreter dependencies unavailable")
        self.assertEqual(
            completed.returncode,
            0,
            msg=f"{class_name} failed (exit {completed.returncode}):\n{output}",
        )

    def test_rmsnorm_skeleton(self) -> None:
        self._run_interpreter_class("RMSNormSkeletonTests")

    def test_moe_dispatch_skeleton(self) -> None:
        self._run_interpreter_class("MoEDispatchSkeletonTests")

    def test_flash_attention_skeleton(self) -> None:
        self._run_interpreter_class("FlashAttentionSkeletonTests")

    def test_gemm_skeleton(self) -> None:
        self._run_interpreter_class("GEMMSkeletonTests")

    def test_bf16_output_skeleton(self) -> None:
        self._run_interpreter_class("BF16OutputSkeletonTests")

    def test_output_dtype_contract(self) -> None:
        self._run_interpreter_class("OutputDtypeContractTests")


if __name__ == "__main__":
    unittest.main()
