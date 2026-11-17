---
type: Example
title: MoE Dispatch 代码骨架
description: MoE Token Scatter + Expert GEMM 两阶段代码骨架。适用 MoE 专家路由与 top-k 分发场景。
tags: [task.implementation, topic.compute.indexing, topic.compute.composite]
status: stable
sources:
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/Indexing_Ops/gather.md
  role: primary
- resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/docs/zh/triton_api/Linear_Algebra_Ops/dot.md
  role: supporting
- resource: https://gitcode.com/zhou_huaman/cannbot-skills_5171_kkb_pr/blob/e195a77116202190f6b706d8ea802b712e8cc3f4/ops/triton-knowledge-retrieval/knowledge/pages/skeletons/moe_dispatch.py
  role: example
created_at: '2026-08-12T00:00:00Z'
updated_at: '2026-11-17T01:55:07Z'
platforms: [a2, a3]
---
# MoE Dispatch 代码骨架

> 经验来源：[exp_gs_bin_003](../optimizations/experiences/gather_scatter_experiences.md#exp_gs_bin_003) Binned dispatch (35%), [exp_gs_bin_005](../optimizations/experiences/gather_scatter_experiences.md#exp_gs_bin_005) work-stealing (30%)

## 关键设计点

1. **两阶段设计**：Phase 1 Token Scatter（按 expert 分组写入 buffer）→ Phase 2 Expert GEMM（每个 expert 独立矩阵乘）
2. **Binned Dispatch**：按 expert ID 排序后连续写入，减少随机 scatter 开销
3. **Slot 预计算**：host 侧预计算每个 token 在 expert buffer 中的 slot，kernel 只做写入
4. **BLOCK_H tiling**：hidden_dim 维度分块处理，每块独立 scatter
5. **容量溢出契约**：超过 `max_capacity` 的 token 记 `slot=-1`；scatter 跳过写入（不覆盖专家内有效 token），gather 跳过写回，`output` 预置 0，溢出 token 的输出因此有确定值。`slots` 必须独立分配为有符号 `int32`，不能用 `full_like(routing, -1)`：无符号 routing（如 `uint8`）会把 `-1` 回绕成 `255`，绕过 `slot_id < 0` 判断并访问专家 buffer 范围之外的 slot。若业务不允许丢弃，应在 host 侧检测到 `slot=-1` 后显式报错

## 核心结构

```python
# Phase 1: Token Scatter
@triton.jit
def token_scatter_kernel(tokens_ptr, expert_buf_ptr, routing_ptr,
                         slot_ptr, num_tokens, hidden_dim, ...):
    pid = tl.program_id(0)
    # 每个 program 处理一个 token（本骨架按 top-1 路由）
    # 按 slot 写入 expert_buf

# Phase 2: Expert GEMM
# 每个 expert 独立调用 GEMM kernel
```

## 完整骨架

以下为 KKB 骨架源码全文（固定提交 `e195a77`），已内联到知识卡，避免迁移后 `skeletons/` 路径失效。

```python
"""
骨架：MoE Token Dispatch（Scatter + Expert GEMM）
适用：MoE 专家路由，top-k 分发
经验：exp_gs_bin_003 Binned dispatch (35%), exp_gs_bin_005 work-stealing (30%)
参考：ops/gather_scatter.md, ops/fused_ops.md Fusion-6
约束：[hardware/constraints_cheatsheet]
"""

import torch
import triton
import triton.language as tl


# ────────────────────────────────────────────────────────────────
# Phase 1: Token Scatter（按 expert 分组写入 expert buffer）
# ────────────────────────────────────────────────────────────────

@triton.jit
def token_scatter_kernel(
    tokens_ptr,         # [num_tokens, hidden_dim]
    expert_buf_ptr,     # [num_experts * max_capacity, hidden_dim]（输出）
    routing_ptr,        # [num_tokens]  每个 token 的 expert ID（本骨架按 top-1；top-k 时按 (token, k) 对展开）
    slot_ptr,           # [num_tokens]  每个 token 在 expert buffer 中的 slot，-1 表示容量溢出
    num_tokens,
    hidden_dim,
    max_capacity: tl.constexpr,
    BLOCK_H: tl.constexpr,   # hidden_dim 每次处理的列数
):
    # 每个 program 处理一个 token（本骨架按 top-1 路由）
    pid = tl.program_id(0)
    if pid >= num_tokens:
        return

    expert_id = tl.load(routing_ptr + pid)
    slot_id = tl.load(slot_ptr + pid)
    if slot_id < 0:
        return  # 容量溢出：该 token 被丢弃，不能覆盖 expert buffer 中的有效 slot
    dst_row = expert_id * max_capacity + slot_id

    offs = tl.arange(0, BLOCK_H)
    for h_start in range(0, hidden_dim, BLOCK_H):
        h_offs = h_start + offs
        mask = h_offs < hidden_dim
        x = tl.load(tokens_ptr + pid * hidden_dim + h_offs, mask=mask, other=0.0)
        tl.store(expert_buf_ptr + dst_row * hidden_dim + h_offs, x, mask=mask)


# ────────────────────────────────────────────────────────────────
# Phase 2: Expert GEMM（每个 expert 独立矩阵乘）
# 注意：此处调用 ops/matmul.md 中的 matmul kernel，按 expert 批量执行
# ────────────────────────────────────────────────────────────────

@triton.jit
def expert_gemm_kernel(
    input_ptr,       # [num_experts * max_capacity, hidden_dim]
    weight_ptr,      # [num_experts, hidden_dim, ffn_dim]（各专家权重）
    output_ptr,      # [num_experts * max_capacity, ffn_dim]
    token_counts_ptr,  # [num_experts] 每个 expert 实际收到的 token 数
    max_capacity,
    hidden_dim,
    ffn_dim,
    BLOCK_M: tl.constexpr,
    BLOCK_N: tl.constexpr,
    BLOCK_K: tl.constexpr,
):
    # pid_expert: 负责哪个 expert
    # pid_tile: 在该 expert 的输出矩阵中负责哪个 (m_tile, n_tile)
    pid_expert = tl.program_id(1)
    pid_tile = tl.program_id(0)

    token_count = tl.load(token_counts_ptr + pid_expert)
    if token_count == 0:
        return  # 空 expert，跳过

    num_m = tl.cdiv(token_count, BLOCK_M)
    num_n = tl.cdiv(ffn_dim, BLOCK_N)
    m_id = pid_tile // num_n
    n_id = pid_tile % num_n

    if m_id >= num_m:
        return

    offs_m = m_id * BLOCK_M + tl.arange(0, BLOCK_M)
    offs_n = n_id * BLOCK_N + tl.arange(0, BLOCK_N)
    offs_k = tl.arange(0, BLOCK_K)

    input_base = input_ptr + pid_expert * max_capacity * hidden_dim
    weight_base = weight_ptr + pid_expert * hidden_dim * ffn_dim

    acc = tl.zeros([BLOCK_M, BLOCK_N], dtype=tl.float32)
    for k in range(0, tl.cdiv(hidden_dim, BLOCK_K)):
        k_offs = k * BLOCK_K + offs_k
        a = tl.load(input_base + offs_m[:, None] * hidden_dim + k_offs[None, :],
                    mask=(offs_m[:, None] < token_count) & (k_offs[None, :] < hidden_dim),
                    other=0.0)
        b = tl.load(weight_base + k_offs[:, None] * ffn_dim + offs_n[None, :],
                    mask=(k_offs[:, None] < hidden_dim) & (offs_n[None, :] < ffn_dim),
                    other=0.0)
        acc += tl.dot(a, b)

    output_base = output_ptr + pid_expert * max_capacity * ffn_dim
    tl.store(output_base + offs_m[:, None] * ffn_dim + offs_n[None, :],
             acc.to(output_ptr.dtype.element_ty),
             mask=(offs_m[:, None] < token_count) & (offs_n[None, :] < ffn_dim))


# ────────────────────────────────────────────────────────────────
# Phase 3: Token Gather（从 expert buffer 收集回 token 顺序）
# ────────────────────────────────────────────────────────────────

@triton.jit
def token_gather_kernel(
    expert_out_ptr,  # [num_experts * max_capacity, ffn_dim]
    output_ptr,      # [num_tokens, ffn_dim]
    routing_ptr,     # [num_tokens] 每个 token 的 expert ID
    slot_ptr,        # [num_tokens] 每个 token 在 expert buffer 中的 slot，-1 表示容量溢出
    num_tokens,
    ffn_dim,
    max_capacity: tl.constexpr,
    BLOCK_H: tl.constexpr,
):
    pid = tl.program_id(0)
    if pid >= num_tokens:
        return

    expert_id = tl.load(routing_ptr + pid)
    slot_id = tl.load(slot_ptr + pid)
    if slot_id < 0:
        return  # 容量溢出 token：output 预置为 0，直接跳过；不能回读 slot 0 的专家输出
    src_row = expert_id * max_capacity + slot_id

    offs = tl.arange(0, BLOCK_H)
    for h_start in range(0, ffn_dim, BLOCK_H):
        h_offs = h_start + offs
        mask = h_offs < ffn_dim
        x = tl.load(expert_out_ptr + src_row * ffn_dim + h_offs, mask=mask, other=0.0)
        tl.store(output_ptr + pid * ffn_dim + h_offs, x, mask=mask)


# ────────────────────────────────────────────────────────────────
# 顶层调度函数
# ────────────────────────────────────────────────────────────────

def moe_dispatch(
    tokens: torch.Tensor,          # [num_tokens, hidden_dim]
    expert_weights: torch.Tensor,  # [num_experts, hidden_dim, ffn_dim]
    routing: torch.Tensor,         # [num_tokens] top-1 expert ID
    max_capacity: int,             # 每个 expert 的最大 token 容量
) -> torch.Tensor:
    num_tokens, hidden_dim = tokens.shape
    num_experts, _, ffn_dim = expert_weights.shape
    BLOCK_H = min(triton.next_power_of_2(hidden_dim), 1024)

    # 计算每个 expert 的 slot（token 在该 expert buffer 中的位置）
    # -1 是容量溢出标记：scatter/gather 跳过该 token，output 中保持 0。
    # slots 独立分配为有符号 int32：不能 full_like(routing)，否则 uint8 routing
    # 会把 -1 回绕成 255，绕过 kernel 的 slot_id < 0 判断并越界访问专家 buffer。
    slots = torch.full(routing.shape, -1, device=routing.device, dtype=torch.int32)
    token_counts = torch.zeros(num_experts, dtype=torch.int32, device=tokens.device)
    for i in range(num_tokens):  # 实际中用 CUDA/NPU kernel 计算
        e = routing[i].item()
        if token_counts[e] < max_capacity:
            slots[i] = token_counts[e]
            token_counts[e] += 1

    # Phase 1: Scatter
    expert_buf = torch.zeros(num_experts * max_capacity, hidden_dim,
                             device=tokens.device, dtype=tokens.dtype)
    token_scatter_kernel[(num_tokens,)](
        tokens, expert_buf, routing, slots,
        num_tokens, hidden_dim, max_capacity=max_capacity, BLOCK_H=BLOCK_H,
    )

    # Phase 2: Expert GEMM
    expert_out = torch.zeros(num_experts * max_capacity, ffn_dim,
                             device=tokens.device, dtype=tokens.dtype)
    max_tiles = triton.cdiv(max_capacity, 128) * triton.cdiv(ffn_dim, 128)
    expert_gemm_kernel[(max_tiles, num_experts)](
        expert_buf, expert_weights, expert_out, token_counts,
        max_capacity, hidden_dim, ffn_dim,
        BLOCK_M=128, BLOCK_N=128, BLOCK_K=256,
    )

    # Phase 3: Gather（预置 0，保证容量溢出 token 的输出有确定值）
    output = torch.zeros(num_tokens, ffn_dim, device=tokens.device, dtype=tokens.dtype)
    token_gather_kernel[(num_tokens,)](
        expert_out, output, routing, slots,
        num_tokens, ffn_dim, max_capacity=max_capacity, BLOCK_H=BLOCK_H,
    )

    return output
```

