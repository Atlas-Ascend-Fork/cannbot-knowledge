---
type: Example
title: RMSNorm 融合代码骨架
description: 支持 Skip Add + RMSNorm 融合的代码骨架。适用 fp16/bf16，任意 batch/seq/hidden 维度。
tags: [task.implementation, topic.compute.normalization, topic.compute.composite]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/third_party/ascend/unittest/pytest_ut/test_rms_norm.py
  role: example
- resource: https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/skeletons/rmsnorm_fused.py
  role: example
created_at: '2026-08-12T00:00:00Z'
updated_at: '2026-11-13T01:54:47Z'
platforms: [a2, a3]

---
# RMSNorm 融合代码骨架

> 经验来源：[exp_rmsnorm_npu_001](../optimizations/experiences/normalization_experiences.md#exp_rmsnorm_npu_001) 列分块 (35%), [exp_skip_layernorm_001](../optimizations/experiences/normalization_experiences.md#exp_skip_layernorm_001) Skip+Norm (30%)

## 关键设计点

1. **Auto BLOCK_SIZE_N**：用 `@triton.heuristics` 自动选整行或最大 4096，不超 UB
2. **Column Blocking**：hidden_dim 超过 UB 容量时分列处理，两次 pass 完成（一次 mean_sq，一次 normalize）
3. **Skip Add 融合**：`HAS_RESIDUAL=True` 时 `x + residual` 与 RMSNorm 在单 kernel 完成，避免中间 HBM 写；整行与大 hidden 列分块两个 kernel 都支持 residual，并写出 `residual_out`
4. **Persistent Kernel**：用 grid-stride loop 确保核数固定，减少 launch 开销
5. **fp32 精度**：mean_sq 在 fp32 中累加，`tl.rsqrt` 倒数平方根

## 核心结构

```python
@triton.heuristics({'BLOCK_SIZE_N': lambda args: ...})
@triton.jit
def rmsnorm_kernel(x_ptr, residual_ptr, weight_ptr, out_ptr,
                   residual_out_ptr, M, N, ...,
                   HAS_RESIDUAL: tl.constexpr, BLOCK_SIZE_N: tl.constexpr):
    pid = tl.program_id(0)
    # grid-stride over rows → load row + (optional residual add)
    # → compute mean_sq in fp32 → rsqrt → scale by weight → store
```

## 完整骨架

以下为 KKB 骨架源码全文（固定提交 `e195a77`），已内联到知识卡，避免迁移后 `skeletons/` 路径失效。

```python
"""
骨架：RMSNorm（融合变体：支持 Skip Add + RMSNorm）
适用：fp16/bf16，任意 batch/seq/hidden
经验：exp_rmsnorm_001(086) Persistent (35%), exp_rmsnorm_npu_001(093) 列分块 (35%)
       exp_skip_layernorm_001(118) Skip+Norm融合 (30%)
参考：ops/normalization.md, techniques/persistent_kernels.md
约束：[hardware/constraints_cheatsheet]
"""

import torch
import triton
import triton.language as tl
from triton.runtime import driver


@triton.heuristics({
    # 自动选 BLOCK_SIZE_N：尽量一次装入整行，不超 UB（fp32: ~49K elements）
    'BLOCK_SIZE_N': lambda args: min(
        triton.next_power_of_2(args['N']),
        4096  # 上限：4096 * 4B(fp32) = 16KB，远小于 192KB UB
    ),
})
@triton.jit
def rmsnorm_kernel(
    x_ptr,            # 输入 [M, N]
    residual_ptr,     # Skip 残差输入（可选，HAS_RESIDUAL=True 时使用）
    weight_ptr,       # 归一化权重 [N]
    out_ptr,          # 输出 [M, N]
    residual_out_ptr, # Skip Add 后的中间结果输出（可选）
    M, N,
    eps: tl.constexpr,
    HAS_RESIDUAL: tl.constexpr,   # 是否融合 Skip Add
    BLOCK_SIZE_N: tl.constexpr,
):
    # ── Persistent kernel：固定 grid = num_aicores，grid-stride 遍历行 ──
    pid = tl.program_id(0)
    num_programs = tl.num_programs(0)

    # 权重只加载一次，复用于此 program 处理的所有行
    offs_n = tl.arange(0, BLOCK_SIZE_N)
    w_mask = offs_n < N
    weight = tl.load(weight_ptr + offs_n, mask=w_mask, other=0.0).to(tl.float32)

    for row in range(pid, M, num_programs):
        x_ptrs = x_ptr + row * N + offs_n
        x = tl.load(x_ptrs, mask=w_mask, other=0.0).to(tl.float32)

        if HAS_RESIDUAL:
            res_ptrs = residual_ptr + row * N + offs_n
            residual = tl.load(res_ptrs, mask=w_mask, other=0.0).to(tl.float32)
            x = x + residual
            # 写出 skip add 中间结果（后续层可能需要）
            tl.store(residual_out_ptr + row * N + offs_n, x, mask=w_mask)

        # ── Two-pass RMSNorm ──────────────────────────────────────
        # Pass 1: 计算 variance = mean(x^2)（fp32 累加）
        x_sq = x * x
        var = tl.sum(x_sq, axis=0) / N   # scalar

        # Pass 2: 归一化
        rstd = 1.0 / tl.sqrt(var + eps)  # rsqrt 替代 sqrt+div
        x_norm = x * rstd
        out = x_norm * weight

        tl.store(out_ptr + row * N + offs_n, out.to(out_ptr.dtype.element_ty), mask=w_mask)


# ── 大 hidden dim 变体（n_cols > 4096，需列分块 two-pass）──────────
@triton.jit
def rmsnorm_large_hidden_kernel(
    x_ptr, residual_ptr, weight_ptr, out_ptr, residual_out_ptr,
    M, N,
    eps: tl.constexpr,
    HAS_RESIDUAL: tl.constexpr,   # 是否融合 Skip Add（与 rmsnorm_kernel 语义一致）
    BLOCK_SIZE_N: tl.constexpr,   # 每次处理的列数（满足 UB 约束）
):
    pid = tl.program_id(0)
    num_programs = tl.num_programs(0)

    for row in range(pid, M, num_programs):
        # Pass 1: 分块累加 sum((x + residual)^2)；融合 residual 时顺带写出 skip add 结果
        var_acc = tl.zeros([BLOCK_SIZE_N], dtype=tl.float32)
        for col_start in range(0, N, BLOCK_SIZE_N):
            offs = col_start + tl.arange(0, BLOCK_SIZE_N)
            mask = offs < N
            x = tl.load(x_ptr + row * N + offs, mask=mask, other=0.0).to(tl.float32)
            if HAS_RESIDUAL:
                residual = tl.load(residual_ptr + row * N + offs, mask=mask, other=0.0).to(tl.float32)
                x = x + residual
                tl.store(residual_out_ptr + row * N + offs, x, mask=mask)
            var_acc += x * x
        var = tl.sum(var_acc, axis=0) / N
        rstd = 1.0 / tl.sqrt(var + eps)

        # Pass 2: 分块归一化；residual 重新加载并相加，保证与 Pass 1 使用同一份 fp32 数据
        for col_start in range(0, N, BLOCK_SIZE_N):
            offs = col_start + tl.arange(0, BLOCK_SIZE_N)
            mask = offs < N
            x = tl.load(x_ptr + row * N + offs, mask=mask, other=0.0).to(tl.float32)
            if HAS_RESIDUAL:
                residual = tl.load(residual_ptr + row * N + offs, mask=mask, other=0.0).to(tl.float32)
                x = x + residual
            w = tl.load(weight_ptr + offs, mask=mask, other=0.0).to(tl.float32)
            out = x * rstd * w
            tl.store(out_ptr + row * N + offs, out.to(out_ptr.dtype.element_ty), mask=mask)


def rmsnorm(
    x: torch.Tensor,          # [M, N]
    weight: torch.Tensor,     # [N]
    residual: torch.Tensor = None,  # [M, N]，可选 Skip Add
    eps: float = 1e-5,
):
    assert x.is_contiguous()
    M, N = x.shape
    out = torch.empty_like(x)
    residual_out = torch.empty_like(x) if residual is not None else None

    # 获取 AI Core 数量（Persistent kernel 的 grid 大小）
    device = x.device
    try:
        props = driver.active.utils.get_device_properties(device.index)
        num_cores = props["multiprocessor_count"]
    except Exception:
        num_cores = 20  # 910b2 默认值

    grid_size = min(M, num_cores)

    if N <= 4096:
        rmsnorm_kernel[(grid_size,)](
            x, residual if residual is not None else x,
            weight, out,
            residual_out if residual_out is not None else out,
            M, N,
            eps=eps,
            HAS_RESIDUAL=(residual is not None),
        )
    else:
        # 列分块：BLOCK_SIZE_N * 4B(fp32) ≤ ~16KB
        BLOCK_N = min(triton.next_power_of_2(N), 4096)
        rmsnorm_large_hidden_kernel[(grid_size,)](
            x, residual if residual is not None else x,
            weight, out,
            residual_out if residual_out is not None else out,
            M, N,
            eps=eps,
            HAS_RESIDUAL=(residual is not None),
            BLOCK_SIZE_N=BLOCK_N,
        )

    return (out, residual_out) if residual is not None else out
```

