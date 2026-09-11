---
type: Runbook
title: 昇腾 Triton kernel grid 首维溢出 CoreDim UINT16 上界（大批量/长序列）
description: 若你正观测到上述症状，且该 kernel 的 launch grid 第一维随 batch/序列长度线性增长（典型为「一行 token 一个 program」的逐行规约 kernel，如 (RMS)Norm / LayerNorm / gated-norm），则本页适用。
tags:
- task.debugging
- topic.model_architecture
- topic.attention
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/issues/3548
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 昇腾 Triton kernel grid 首维溢出 CoreDim UINT16 上界（大批量/长序列）

## 信号（现象）

在昇腾 NPU 上启动一个 Triton kernel（`torch_npu` triton 后端），运行到**大批量 / 长序列**规模时抛出运行时异常：

```
coreDim=xxx can't be greater than UINT16_MAX.
```

或框架层报为 `invalid CoreDim`。此前小批量 / 短序列同一 kernel 正常，症状只在把 batch_size 或输出长度推高、并发规约行数冲高后才出现。对照面：同一 kernel 的上游 CUDA/GPU 版本从不报此错。

若你正观测到上述症状，且该 kernel 的 launch grid 第一维随 batch/序列长度线性增长（典型为「一行 token 一个 program」的逐行规约 kernel，如 (RMS)Norm / LayerNorm / gated-norm），则本页适用。

## 触发条件

- **后端**：Triton kernel 跑在昇腾 NPU 上（`torch_npu` triton），grid 第一维被映射为 NPU 的 **CoreDim**。
- **grid 形状**：kernel 以 `grid = (M, ...)` 启动，`M` = 参与规约的 token 行数（batch × seq 展平），即每行 token 分配一个 program/core。
- **规模阈值**：`M > 65535`（UINT16_MAX）。大批量 + 长生成会把 `M` 推过此线——例如高并发解码使 KV cache 占用逼近 100%、同一步待规约行数冲高时。
- 昇腾侧固有：CoreDim 取值上界为 `UINT16_MAX = 65535`；此约束不随硬件型号/CANN 版本放宽，是 NPU triton launch 的硬边界。

## 根因

Triton kernel 的 **grid 第一维在昇腾上被映射为 NPU 的 CoreDim，其取值上界是 `UINT16_MAX = 65535`**。当 kernel 采用「一 program 处理一行」的逐行规约模式（`grid = (M, ngroups)`，`M` 为 token 行数）时，一旦 `M` 超过 65535，请求的 CoreDim 超界，NPU 直接拒绝并抛 `coreDim=... can't be greater than UINT16_MAX`。

这是 **backend_incompatibility**：同款 kernel 在 GPU 上 grid 首维上限约 `2^31-1`，几乎不可能溢出，因此直接从上游移植的 CUDA 版 kernel 未针对 NPU 的 CoreDim 上界做适配。根因不在模型逻辑、也不在数值精度，而在 launch 维度与后端物理核数编址位宽的错配。

## 修法

把「grid 首维 = M」的逐行 kernel 改成 **「grid 首维截顶到 65535 + kernel 内按 stride 跨步循环覆盖剩余行」**，两处配套改动缺一不可：

1. **launch 侧截顶 grid 首维**：定义 `MAX_CORES = 65535`，`grid = (M if M < MAX_CORES else MAX_CORES, ngroups)`，并把上限作为 `constexpr`（`N_CORES = MAX_CORES`）传入 kernel。这样启动的 program 数永不超过 65535，绕过 CoreDim 上界。

   ```python
   MAX_CORES = 65535
   grid = (M if M < MAX_CORES else MAX_CORES, ngroups)
   layer_norm_fwd_kernel[grid](x, ..., N_CORES=MAX_CORES, num_warps=num_warps)
   ```

2. **kernel 内跨步循环覆盖剩余行**：截顶后 program 数 `< M`，单个 program 需处理多行。用 `BLOCK_ROWS = M if M < N_CORES else N_CORES` 求每轮跨度，`n_iters = M // BLOCK_ROWS`、`remain = M % BLOCK_ROWS`；前 `remain` 个 row 多做一轮（`if row < remain: n_iters += 1`）以吃掉余数行；循环内以 `i * BLOCK_ROWS * stride_x_row + row * stride_x_row` 为基址跨步取址，逐行完成 mean/rstd 规约、(RMS)Norm、以及可选的 gating（如 `z * sigmoid(z)`）写回。

   ```python
   row = tl.program_id(0)
   BLOCK_ROWS = M if M < N_CORES else N_CORES
   n_iters = M // BLOCK_ROWS
   remain = M % BLOCK_ROWS
   if row < remain:
       n_iters = n_iters + 1
   for i in tl.range(n_iters):
       X_base = X + (i * BLOCK_ROWS * stride_x_row) + row * stride_x_row + group * N
       # ... 逐行 (RMS)Norm + 可选 gating 写回 ...
   ```

功能上与原逐行 kernel **等价**——只是把「一 program 一行」改成「一 program 多行、每隔 65535 步取址一次」，规约与归一化语义不变。

**通用抓手**：任何在 NPU 上以「行数当 grid 首维」启动、且行数可能随 batch/序列长度超过 65535 的 Triton 逐行 kernel，都要用「grid 首维 clamp 到 65535 + kernel 内 stride 循环」这一范式；不要假设 GPU 上不会溢出就照搬 grid。fork/vendored kernel 若直接从上游 CUDA 实现 import，须复核其 launch grid 维度上界是否踩 CoreDim 线。

### 参考实现及其约束

- **参考实现**：vllm-ascend `vllm_ascend/ops/fla.py` 的 `layer_norm_fwd_kernel`（FLA = flash linear attention），服务 [qwen3-next](../../concepts/models/qwen3_next.md) 的 [gated-deltanet](../../concepts/modules/gated_deltanet.md) 线性注意力路径中的 gated (RMS)Norm；对应线性递归核见 [recurrent-gated-delta-rule](../../concepts/kernels/recurrent_gated_delta_rule.md)。该 kernel 原本从上游 vLLM `vllm.model_executor.layers.fla.ops.layernorm_guard` 直接 import，`_layer_norm_fwd` 用 `grid = (M, ngroups)` 启动，未适配 NPU；vllm-ascend 在本仓 fork 了它并加上截顶 + 跨步循环。
- **约束（属该参考实现、非技术本身）**：`MAX_CORES = 65535` 是该 fork 的硬编码常量；复现规模为 Qwen3-Next-80B-A3B-Instruct、`--tensor-parallel-size 4 --max-model-len 32000 --enforce-eager`，用大批量 + 长输出（aisbench `batch_size=512`、`max_out_len=30000`）把 `M` 推过 65535。`z * sigmoid(z)` gating 是该 gated-norm 特有的写回步骤，其他逐行 kernel 按各自算子替换即可。
- **验证 / 回退**：修后在同一大批量、长输出、KV cache 占用达 100% 的场景下不再抛 CoreDim 异常，全部请求正常完成（吞吐为仓自报，无独立前后定量复测）。若怀疑跨步循环引入数值偏差，可在 `M < 65535`（不触发截顶、退化为逐行）与 `M > 65535` 两档下对拍归一化输出确认等价。

## Evidence

- [vllm-ascend-issue-3548-bug-qwen3-next-has-a-runtime-bug-in-layer-norm-fwd-kernel-which-has-inva](https://github.com/vllm-project/vllm-ascend/issues/3548) — issue（closed，作者收尾确认已由对应修复 PR 解决）+ 修复 PR（state=MERGED，merge sha `534f32d27c0cc48731fbdae3701fbb6c3bb4332a`，2025-10-21，`vllm_ascend/ops/fla.py`）。
- 核心断言（`grid = (M, ngroups)` 溢出 CoreDim / 修法为截顶 + 循环）为合并态 diff 内容；根因（CoreDim = UINT16_MAX 上界）由 issue 标题 `invalid CoreDim`、PR 测试日志异常文本 `coreDim=xxx can't be greater than UINT16_MAX`、常量 `MAX_CORES=65535` 三点互证。