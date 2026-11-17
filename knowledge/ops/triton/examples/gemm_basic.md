---
type: Example
title: GEMM 基础代码骨架
description: 带 AutoTune 的标准 GEMM kernel 模板（ND layout, trans_b=True）。适用 M≥256, N≥256,
  K≥1024, fp16/bf16。
tags: [task.implementation, topic.compute.composite, topic.tiling, topic.data_movement.memory_access]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/third_party/ascend/tutorials/03-matrix-multiplication.py
  role: example
- resource: https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/skeletons/gemm_basic.py
  role: example
created_at: '2026-08-12T00:00:00Z'
updated_at: '2026-11-13T01:54:47Z'
platforms: [a2, a3]

---
# GEMM 基础代码骨架

> 经验来源：[exp_matmul_001](../optimizations/experiences/matmul_experiences.md#exp_matmul_001) (40% boost), skill_tiling_diagonal (M,N≥512 时)

## 关键设计点

1. **AutoTune 搜索空间**：`BLOCK_M ∈ {128,256}`, `BLOCK_N ∈ {128,256}`, `BLOCK_K=256`, `GROUP_SIZE ∈ {8,16,32}`
2. **列优先 PID 分组**：GROUP_SIZE 控制相邻 PID 的 Core 分配，共享 L2 中 A 矩阵数据
3. **2D Block Pointer**：`tl.make_block_ptr` + `order=(1,0)` 行主序访问，编译器生成更优地址指令
4. **L0C 寄存器复用**：`acc` 保留在 L0C 中，K 轴迭代完成后一次性写回
5. **fp32 累加**：`acc = tl.zeros([BLOCK_M, BLOCK_N], dtype=tl.float32)`，最终按输出指针 dtype 转换（`acc.to(c_ptr.dtype.element_ty)`，fp16/bf16 通用）

## 核心结构

```python
@triton.autotune(configs=[...], key=['M', 'N', 'K'])
@triton.jit
def matmul_kernel(a_ptr, b_ptr, c_ptr, M, N, K,
                  stride_am, stride_ak, stride_bk, stride_bn,
                  stride_cm, stride_cn,
                  BLOCK_M: tl.constexpr, BLOCK_N: tl.constexpr,
                  BLOCK_K: tl.constexpr, GROUP_SIZE: tl.constexpr):
    pid = tl.program_id(0)
    # 列优先 PID → (pid_m, pid_n) 映射
    # tl.make_block_ptr → L0C acc → K 轴循环 tl.dot → tl.store
```

## 完整骨架

以下为 KKB 骨架源码全文（固定提交 `e195a77`），已内联到知识卡，避免迁移后 `skeletons/` 路径失效。

```python
"""
骨架：GEMM（矩阵乘法）基础模板
适用：M≥256, N≥256, K≥1024, fp16/bf16, NN 布局
经验：exp_matmul_001 (40%), skill_tiling_diagonal（M,N≥512 时）
约束检查：[hardware/constraints_cheatsheet]
"""

import torch
import triton
import triton.language as tl


# ── AutoTune 配置 ────────────────────────────────────────────────
# 满足 512B 行宽对齐（fp16/bf16: BLOCK_N≥256）
# GROUP_SIZE 至少提供 8/16/32 三档
configs = [
    triton.Config({'BLOCK_M': bm, 'BLOCK_N': bn, 'BLOCK_K': 256, 'GROUP_SIZE': gs},
                  num_stages=2, num_warps=4)
    for bm in [128, 256]
    for bn in [128, 256]
    for gs in [8, 16, 32]
]


@triton.autotune(configs=configs, key=['M', 'N', 'K'])
@triton.jit
def matmul_kernel(
    a_ptr, b_ptr, c_ptr,
    M, N, K,
    stride_am, stride_ak,
    stride_bk, stride_bn,
    stride_cm, stride_cn,
    BLOCK_M: tl.constexpr,
    BLOCK_N: tl.constexpr,
    BLOCK_K: tl.constexpr,
    GROUP_SIZE: tl.constexpr,
):
    # ── PID → (m_id, n_id)：对角映射（M,N≥512 时消除 L2 bank conflict）──
    pid = tl.program_id(0)
    num_m_blocks = tl.cdiv(M, BLOCK_M)
    num_n_blocks = tl.cdiv(N, BLOCK_N)
    num_blocks_in_group = GROUP_SIZE * num_n_blocks
    group_id = pid // num_blocks_in_group
    first_m = group_id * GROUP_SIZE
    group_m_size = min(num_m_blocks - first_m, GROUP_SIZE)
    m_id = first_m + (pid % group_m_size)
    n_id = (pid % num_blocks_in_group) // group_m_size

    # ── 指针计算 ──────────────────────────────────────────────────
    offs_m = m_id * BLOCK_M + tl.arange(0, BLOCK_M)
    offs_n = n_id * BLOCK_N + tl.arange(0, BLOCK_N)
    offs_k = tl.arange(0, BLOCK_K)

    a_ptrs = a_ptr + offs_m[:, None] * stride_am + offs_k[None, :] * stride_ak
    b_ptrs = b_ptr + offs_k[:, None] * stride_bk + offs_n[None, :] * stride_bn

    # ── 累加（fp32） ──────────────────────────────────────────────
    acc = tl.zeros([BLOCK_M, BLOCK_N], dtype=tl.float32)
    for k in range(0, tl.cdiv(K, BLOCK_K)):
        # care_padding=False：当 padding 不影响结果时，避免 MTE2→Vector 同步屏障
        a = tl.load(a_ptrs, mask=(offs_m[:, None] < M) & (offs_k[None, :] < K - k * BLOCK_K),
                    other=0.0, cache_modifier=".cg")
        b = tl.load(b_ptrs, mask=(offs_k[:, None] < K - k * BLOCK_K) & (offs_n[None, :] < N),
                    other=0.0, cache_modifier=".cg")
        acc += tl.dot(a, b)
        a_ptrs += BLOCK_K * stride_ak
        b_ptrs += BLOCK_K * stride_bk

    # ── Store ─────────────────────────────────────────────────────
    c_ptrs = c_ptr + offs_m[:, None] * stride_cm + offs_n[None, :] * stride_cn
    mask = (offs_m[:, None] < M) & (offs_n[None, :] < N)
    tl.store(c_ptrs, acc.to(c_ptr.dtype.element_ty), mask=mask)


def matmul(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    assert a.shape[1] == b.shape[0], "K dim mismatch"
    assert a.is_contiguous() and b.is_contiguous(), "Inputs must be contiguous"
    M, K = a.shape
    K, N = b.shape
    c = torch.empty((M, N), device=a.device, dtype=a.dtype)

    # grid_size ≤ num_ai_cores 约束（TRITON_ALL_BLOCKS_PARALLEL 解决多轮调度问题）
    grid = lambda meta: (triton.cdiv(M, meta['BLOCK_M']) * triton.cdiv(N, meta['BLOCK_N']),)
    matmul_kernel[grid](
        a, b, c,
        M, N, K,
        a.stride(0), a.stride(1),
        b.stride(0), b.stride(1),
        c.stride(0), c.stride(1),
    )
    return c


# ── 扩展变体（取消注释以使用）────────────────────────────────────

# 融合激活函数（在 acc store 前施加）：
#   acc = tl.sigmoid(acc) * acc  # SiLU
#   acc = 0.5 * acc * (1 + tl.math.erf(acc * 0.7071067811865476))  # GELU

# 融合 Bias（在 acc store 前加 bias 向量）：
#   bias = tl.load(bias_ptr + offs_n, mask=offs_n < N, other=0.0)
#   acc += bias[None, :]
```

## 触发条件

- 计算图含 `torch.matmul`/`torch.mm`/`torch.bmm`/`F.linear`
- M≥128, N≥128, K≥256
- fp16/bf16, ND layout, trans_b=True

