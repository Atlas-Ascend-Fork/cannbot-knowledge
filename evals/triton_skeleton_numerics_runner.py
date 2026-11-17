# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Triton interpreter 数值用例的运行器。

本文件不匹配默认的 `test_*.py` 发现模式，只由 test_triton_skeleton_numerics.py
在独立子进程中调用。torch/triton 是可选依赖；缺失时以 77 退出，由调用方转换为
unittest.SkipTest。

Triton interpreter 不支持 bf16 算术（bf16 load/add 会得到垃圾值），因此 BF16 场景分两层验证：
静态检查四个骨架不再硬编码 `.to(tl.float16)`，再用一个 fp32 -> bf16 的 cast kernel 验证
`ptr.dtype.element_ty` 的存储语义（99840 在 bf16 中有限、在 fp16 中溢出为 Inf）。
"""

from __future__ import annotations

import argparse
import functools
import linecache
import os
import re
import sys
import unittest
from pathlib import Path

# 这是专用子进程：在 import triton 之前打开 interpreter 模式，避免影响调用方的测试进程。
os.environ["TRITON_INTERPRET"] = "1"

try:
    import torch
    import triton
    import triton.language as tl
except ImportError as exc:
    print(f"optional interpreter dependencies unavailable: {exc}", file=sys.stderr)
    raise SystemExit(77)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_ROOT = REPOSITORY_ROOT / "knowledge/ops/triton/examples"
SKELETON_SECTION = "## 完整骨架"
PYTHON_FENCE = re.compile(r"```python\n(.*?)\n```", re.DOTALL)
SKELETON_CARDS = (
    "flash_attention_causal",
    "gemm_basic",
    "moe_dispatch",
    "rmsnorm_fused",
)


def _skeleton_code(name: str) -> str:
    text = (EXAMPLE_ROOT / f"{name}.md").read_text(encoding="utf-8")
    section = text.split(SKELETON_SECTION, 1)[1]
    match = PYTHON_FENCE.search(section)
    if match is None:
        raise AssertionError(f"{name}: inline python skeleton is missing")
    return match.group(1)


@functools.lru_cache(maxsize=None)
def _load_skeleton(name: str) -> dict:
    code = _skeleton_code(name)
    filename = f"<skeleton:{name}>"
    # Triton interpreter 通过 inspect.getsourcelines 重写 kernel AST；
    # 把卡片代码注册到 linecache，保证伪文件名也能取到与行号一致的真实源码。
    linecache.cache[filename] = (
        len(code),
        None,
        code.splitlines(keepends=True),
        filename,
    )
    namespace: dict = {}
    exec(compile(code, filename, "exec"), namespace)
    return namespace


def _jitted_kernel(name: str, kernel_name: str):
    # 两张卡片的 kernel 都由 @triton.autotune 包裹：直接取内层 kernel，
    # 避免在 CPU interpreter 上遍历全部 autotune config。
    return _load_skeleton(name)[kernel_name].fn


class RMSNormSkeletonTests(unittest.TestCase):
    def _reference(self, x: torch.Tensor, weight: torch.Tensor, residual):
        data = x + residual if residual is not None else x
        variance = (data * data).mean(dim=-1, keepdim=True)
        expected = data * torch.rsqrt(variance + 1e-5) * weight
        return data, expected

    def _check(self, hidden: int, residual: bool) -> None:
        torch.manual_seed(hidden + int(residual))
        x = torch.randn(2, hidden, dtype=torch.float32) * 0.5
        weight = torch.randn(hidden, dtype=torch.float32)
        residual_tensor = (
            torch.randn(2, hidden, dtype=torch.float32) if residual else None
        )
        rmsnorm = _load_skeleton("rmsnorm_fused")["rmsnorm"]

        if residual:
            out, residual_out = rmsnorm(x, weight, residual_tensor)
        else:
            out = rmsnorm(x, weight, None)

        data, expected = self._reference(x, weight, residual_tensor)
        torch.testing.assert_close(out, expected, rtol=1e-4, atol=1e-4)
        self.assertEqual(out.dtype, x.dtype)
        if residual:
            self.assertEqual(residual_out.dtype, x.dtype)
            torch.testing.assert_close(
                residual_out, data, rtol=1e-6, atol=0.0
            )

    def test_hidden_boundary_and_large_hidden(self) -> None:
        for hidden in (4096, 4097, 8192):
            for residual in (False, True):
                with self.subTest(hidden=hidden, residual=residual):
                    self._check(hidden, residual)

    def test_fp16_output_uses_input_dtype(self) -> None:
        torch.manual_seed(7)
        x = (torch.randn(2, 32, dtype=torch.float32) * 0.5).to(torch.float16)
        weight = torch.randn(32, dtype=torch.float16)
        out = _load_skeleton("rmsnorm_fused")["rmsnorm"](x, weight, None)
        self.assertEqual(out.dtype, torch.float16)
        expected = (
            x.float()
            * torch.rsqrt((x.float() * x.float()).mean(dim=-1, keepdim=True) + 1e-5)
            * weight.float()
        ).to(torch.float16)
        torch.testing.assert_close(out, expected, rtol=1e-2, atol=1e-2)


class MoEDispatchSkeletonTests(unittest.TestCase):
    def _reference(self, tokens, weights, routing, capacity):
        output = torch.zeros(
            (tokens.shape[0], weights.shape[2]), dtype=tokens.dtype
        )
        counts = [0] * weights.shape[0]
        for i, expert in enumerate(routing.tolist()):
            if counts[expert] < capacity:
                output[i] = tokens[i] @ weights[expert]
                counts[expert] += 1
        return output

    def _check(self, routing, capacity, routing_dtype=torch.int64):
        torch.manual_seed(11)
        tokens = torch.randn(len(routing), 16, dtype=torch.float32)
        weights = torch.randn(2, 16, 16, dtype=torch.float32)
        routing_tensor = torch.tensor(routing, dtype=routing_dtype)
        moe_dispatch = _load_skeleton("moe_dispatch")["moe_dispatch"]

        output = moe_dispatch(tokens, weights, routing_tensor, capacity)
        expected = self._reference(tokens, weights, routing_tensor, capacity)
        torch.testing.assert_close(output, expected, rtol=1e-4, atol=1e-4)

    def test_capacity_not_full(self) -> None:
        self._check([0, 0, 1, 1], capacity=3)

    def test_capacity_exactly_full(self) -> None:
        self._check([0, 0, 1, 1], capacity=2)

    def test_capacity_overflow_drops_token_with_zero_output(self) -> None:
        # 评审用例：routing=[0, 0], capacity=1；溢出 token 必须输出 0，
        # 且不能覆盖 expert 的 slot 0，否则会读到第一个 token 的结果。
        self._check([0, 0], capacity=1)

    def test_capacity_one_over_distinct_experts(self) -> None:
        self._check([0, 1, 0, 1], capacity=1)

    def test_capacity_overflow_with_unsigned_routing(self) -> None:
        # uint8 routing 下 torch.full_like(routing, -1) 会回绕成 255，
        # 绕过 slot_id < 0 并访问专家缓冲区之外；slots 必须独立分配为有符号整型。
        self._check([0, 0], capacity=1, routing_dtype=torch.uint8)


def _run_flash(q, k, v, causal, block_m=64, block_n=128, out_dtype=None):
    kernel = _jitted_kernel("flash_attention_causal", "flash_attention_fwd_kernel")
    batch, q_heads, seq_len, head_dim = q.shape
    if out_dtype is None:
        out = torch.empty_like(q)
    else:
        out = torch.empty(q.shape, dtype=out_dtype)
    grid = (triton.cdiv(seq_len, block_m), batch * q_heads)
    kernel[grid](
        q, k, v, out,
        *q.stride(),
        *k.stride(),
        *v.stride(),
        *out.stride(),
        SEQ_LEN=seq_len,
        HEAD_DIM=head_dim,
        NUM_KV_HEADS=k.shape[1],
        NUM_Q_HEADS=q_heads,
        SCALE=head_dim ** -0.5,
        CAUSAL=causal,
        BLOCK_M=block_m,
        BLOCK_N=block_n,
    )
    return out


class FlashAttentionSkeletonTests(unittest.TestCase):
    def _reference(self, q, k, v, causal):
        repeat = q.shape[1] // k.shape[1]
        k = k.repeat_interleave(repeat, dim=1)
        v = v.repeat_interleave(repeat, dim=1)
        seq_len = q.shape[2]
        scores = torch.matmul(q, k.transpose(-1, -2)) * (q.shape[3] ** -0.5)
        allowed = torch.ones(seq_len, seq_len, dtype=torch.bool)
        if causal:
            allowed = torch.tril(allowed)
        scores = scores.masked_fill(~allowed, float("-inf"))
        return torch.matmul(torch.softmax(scores, dim=-1), v)

    def test_non_causal_ignores_kv_padding_columns(self) -> None:
        # 评审用例：S=1025, BLOCK_N=128, Q=K=0, V=1。
        # padding 列若进入 softmax 分母，结果为 1025/1152≈0.8898，而不是 1。
        seq_len, head_dim, block_n = 1025, 16, 128
        q = torch.zeros(1, 1, seq_len, head_dim, dtype=torch.float32)
        k = torch.zeros(1, 1, seq_len, head_dim, dtype=torch.float32)
        v = torch.ones(1, 1, seq_len, head_dim, dtype=torch.float32)

        out = _run_flash(q, k, v, causal=False, block_n=block_n)
        torch.testing.assert_close(
            out, torch.ones_like(out), rtol=0.0, atol=1e-5
        )

    def test_non_causal_nondivisible_sequence_matches_reference(self) -> None:
        torch.manual_seed(13)
        q = torch.randn(1, 2, 1025, 16, dtype=torch.float32)
        k = torch.randn(1, 1, 1025, 16, dtype=torch.float32)
        v = torch.randn(1, 1, 1025, 16, dtype=torch.float32)

        out = _run_flash(q, k, v, causal=False)
        torch.testing.assert_close(
            out, self._reference(q, k, v, causal=False), rtol=1e-4, atol=1e-4
        )

    def test_causal_nondivisible_sequence_matches_reference(self) -> None:
        torch.manual_seed(17)
        q = torch.randn(1, 2, 1025, 16, dtype=torch.float32)
        k = torch.randn(1, 1, 1025, 16, dtype=torch.float32)
        v = torch.randn(1, 1, 1025, 16, dtype=torch.float32)

        out = _run_flash(q, k, v, causal=True)
        torch.testing.assert_close(
            out, self._reference(q, k, v, causal=True), rtol=1e-4, atol=1e-4
        )

    def test_fp16_output_uses_input_dtype(self) -> None:
        torch.manual_seed(19)
        q = torch.randn(1, 1, 64, 16, dtype=torch.float32).to(torch.float16)
        k = torch.randn(1, 1, 64, 16, dtype=torch.float32).to(torch.float16)
        v = torch.randn(1, 1, 64, 16, dtype=torch.float32).to(torch.float16)

        out = _run_flash(q, k, v, causal=True)
        self.assertEqual(out.dtype, torch.float16)
        expected = self._reference(
            q.float(), k.float(), v.float(), causal=True
        ).to(torch.float16)
        torch.testing.assert_close(out, expected, rtol=1e-2, atol=1e-2)


class GEMMSkeletonTests(unittest.TestCase):
    def test_fp16_store_matches_reference(self) -> None:
        torch.manual_seed(23)
        size = 32
        a = torch.randn(size, size, dtype=torch.float32).to(torch.float16)
        b = torch.randn(size, size, dtype=torch.float32).to(torch.float16)
        out = torch.empty(size, size, dtype=torch.float16)
        kernel = _jitted_kernel("gemm_basic", "matmul_kernel")

        kernel[(1,)](
            a, b, out,
            size, size, size,
            a.stride(0), a.stride(1),
            b.stride(0), b.stride(1),
            out.stride(0), out.stride(1),
            BLOCK_M=size,
            BLOCK_N=size,
            BLOCK_K=size,
            GROUP_SIZE=8,
        )
        self.assertEqual(out.dtype, torch.float16)
        torch.testing.assert_close(
            out, (a.float() @ b.float()).to(torch.float16),
            rtol=1e-2, atol=1e-2,
        )


class BF16OutputSkeletonTests(unittest.TestCase):
    """fp32 计算 + bf16 输出：覆盖 99840 经 fp16 store 会溢出为 Inf 的场景。"""

    LARGE_VALUE = 99840.0

    def test_rmsnorm_bf16_store(self) -> None:
        kernel = _load_skeleton("rmsnorm_fused")["rmsnorm_kernel"]
        x = torch.full((1, 64), 3.0, dtype=torch.float32)
        weight = torch.full((64,), self.LARGE_VALUE, dtype=torch.float32)
        out = torch.empty(1, 64, dtype=torch.bfloat16)

        kernel[(1,)](
            x, x, weight, out, out,
            1, 64,
            eps=1e-5,
            HAS_RESIDUAL=False,
        )
        self.assertTrue(torch.isfinite(out).all())
        self.assertGreater(out[0, 0].item(), 99000.0)

    def test_gemm_bf16_store(self) -> None:
        size = 32
        a = torch.eye(size, dtype=torch.float32)
        b = torch.full((size, size), self.LARGE_VALUE, dtype=torch.float32)
        out = torch.empty(size, size, dtype=torch.bfloat16)
        kernel = _jitted_kernel("gemm_basic", "matmul_kernel")

        kernel[(1,)](
            a, b, out,
            size, size, size,
            a.stride(0), a.stride(1),
            b.stride(0), b.stride(1),
            out.stride(0), out.stride(1),
            BLOCK_M=size,
            BLOCK_N=size,
            BLOCK_K=size,
            GROUP_SIZE=8,
        )
        self.assertTrue(torch.isfinite(out).all())
        self.assertGreater(out[0, 0].item(), 99000.0)

    def test_moe_expert_gemm_bf16_store(self) -> None:
        capacity, hidden, ffn = 1, 16, 16
        inputs = torch.ones(capacity * hidden, dtype=torch.float32)
        weight = torch.full(
            (1, hidden, ffn), self.LARGE_VALUE, dtype=torch.float32
        )
        out = torch.zeros(capacity * ffn, dtype=torch.bfloat16)
        token_counts = torch.tensor([1], dtype=torch.int32)
        kernel = _load_skeleton("moe_dispatch")["expert_gemm_kernel"]

        kernel[(1, 1)](
            inputs, weight, out, token_counts,
            capacity, hidden, ffn,
            BLOCK_M=16, BLOCK_N=16, BLOCK_K=16,
        )
        self.assertTrue(torch.isfinite(out).all())
        # 16 个 99840 相加，fp16 会溢出，bf16 应保持有限。
        self.assertGreater(out[0].item(), 1_000_000.0)

    def test_flash_attention_bf16_store(self) -> None:
        seq_len, head_dim = 64, 16
        q = torch.zeros(1, 1, seq_len, head_dim, dtype=torch.float32)
        k = torch.zeros(1, 1, seq_len, head_dim, dtype=torch.float32)
        v = torch.full(
            (1, 1, seq_len, head_dim), self.LARGE_VALUE, dtype=torch.float32
        )

        out = _run_flash(q, k, v, causal=True, out_dtype=torch.bfloat16)
        self.assertTrue(torch.isfinite(out).all())
        self.assertGreater(out[0, 0, 0, 0].item(), 99000.0)


class OutputDtypeContractTests(unittest.TestCase):
    def test_skeletons_do_not_hardcode_fp16_store(self) -> None:
        for name in SKELETON_CARDS:
            code = _skeleton_code(name)
            with self.subTest(card=name):
                self.assertNotIn(
                    ".to(tl.float16)",
                    code,
                    f"{name}: store must cast to the output pointer dtype",
                )
                self.assertIn(
                    "dtype.element_ty",
                    code,
                    f"{name}: output cast must use ptr.dtype.element_ty",
                )

    def test_bf16_element_type_store_keeps_large_value_finite(self) -> None:
        values = torch.tensor([99840.0, 1234.5, -0.125, 0.0], dtype=torch.float32)

        @triton.jit
        def cast_store(x_ptr, out_ptr, BLOCK: tl.constexpr):
            offsets = tl.arange(0, BLOCK)
            data = tl.load(x_ptr + offsets)
            tl.store(
                out_ptr + offsets,
                data.to(out_ptr.dtype.element_ty),
            )

        bf16_out = torch.zeros(4, dtype=torch.bfloat16)
        cast_store[(1,)](values, bf16_out, BLOCK=4)
        self.assertTrue(torch.isfinite(bf16_out).all())
        self.assertEqual(bf16_out[0].item(), 99840.0)
        torch.testing.assert_close(
            bf16_out.float(), values, rtol=0.004, atol=0.0
        )

        fp16_out = values.to(torch.float16)
        self.assertTrue(torch.isinf(fp16_out[0]))

    def test_bf16_reference_values_are_finite(self) -> None:
        values = torch.tensor([99840.0, 1234.5, -0.125, 0.0], dtype=torch.float32)
        bf16_values = values.to(torch.bfloat16)
        self.assertTrue(torch.isfinite(bf16_values).all())
        torch.testing.assert_close(
            bf16_values.float(), values, rtol=0.004, atol=0.0
        )


TEST_CLASSES = {
    "RMSNormSkeletonTests": RMSNormSkeletonTests,
    "MoEDispatchSkeletonTests": MoEDispatchSkeletonTests,
    "FlashAttentionSkeletonTests": FlashAttentionSkeletonTests,
    "GEMMSkeletonTests": GEMMSkeletonTests,
    "BF16OutputSkeletonTests": BF16OutputSkeletonTests,
    "OutputDtypeContractTests": OutputDtypeContractTests,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--class", dest="class_name", choices=sorted(TEST_CLASSES))
    args = parser.parse_args()
    loader = unittest.defaultTestLoader
    if args.class_name:
        suite = loader.loadTestsFromTestCase(TEST_CLASSES[args.class_name])
    else:
        suite = unittest.TestSuite(
            loader.loadTestsFromTestCase(test_class)
            for test_class in TEST_CLASSES.values()
        )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
