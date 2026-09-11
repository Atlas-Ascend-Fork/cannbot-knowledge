---
type: Concept
title: Ring Attention Overlap
description: 多卡 Ring Attention 的 P2P / AllGather 通信通常与 FA 计算串行，利用率低。Wan2.2-I2V 在此基础上做了**计算-通信掩盖**：异步启动 AllGather 收集远端 KV 的同时，立即用本地 KV 算第一次 FA；AllGather 完成后把远端多个 chunks 合并为一段长序列一次性算第二次 FA；最后用 LSE（Log-Sum-Exp）合并两次输出。实现代码见 `module/unified_sp/core.py`。
tags:
- task.optimization
- topic.attention
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- a2
- a3
---

# Ring Attention Overlap

## Summary

多卡 Ring Attention 的 P2P / AllGather 通信通常与 FA 计算串行，利用率低。Wan2.2-I2V 在此基础上做了**计算-通信掩盖**：异步启动 AllGather 收集远端 KV 的同时，立即用本地 KV 算第一次 FA；AllGather 完成后把远端多个 chunks 合并为一段长序列一次性算第二次 FA；最后用 LSE（Log-Sum-Exp）合并两次输出。实现代码见 [`module/unified_sp/core.py`](https://gitcode.com/weixin_45381022/cann-recipes-infer_wan_overlap/blob/28bf626f6a7db5f1741f37dd0aeb8f90a9bcfde0/module/unified_sp/core.py)。

## Mechanism

![Ring Attention Overlap](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/wan2.2-i2v/figures/overlap.png)
*来源：[`docs/models/wan2.2-i2v/figures/overlap.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/wan2.2-i2v/figures/overlap.png)（cann-recipes-infer @ 2f82d10）*

> 源（Wan2.2-I2V 优化文档）：在多卡 Ring Attention 中，通过异步启动 AllGather 收集其他卡的 KV 数据，同时立即使用本地 KV 计算第一个 FA，让 NPU 计算与网络通信并行执行以掩盖通信延迟；待 AllGather 完成后，将其他多个远程 chunks 合并为一个长序列一次性计算第二个 FA，最后用 LSE（Log-Sum-Exp）算法正确合并两次 attention 输出，达成将通信时间隐藏在本地计算中。

该 overlap 路径由 `SPConfig.use_ring_overlap`（默认 `True`）开关控制，`_forward_core` 在 `ring_world_size > 1` 时据此在 `_ring_attention_overlap` 与对照基线 `_ring_attention_allgather` 之间分派；后者为同步 `dist.all_gather_into_tensor` 收齐全部 KV 后单次整段 `_compute_attention`（计算-通信串行）。overlap 即把 AllGather 与本地 FA 重叠。

LSE 合并（`_merge_two_outputs`）采用在线 softmax 数值稳定式：`lse_new = max(lse_l, lse_r) + log(Σ exp(lse_i - max))`，权重 `w_i = exp(lse_i - lse_new)`，`out = w_l·O_l + w_r·O_r`；两次 FA 均通过 `_npu_attention_with_lse` 调 `torch_npu.npu_fused_infer_attention_score` 并置 `softmax_lse_flag=True` 取回 lse。

```mermaid
sequenceDiagram
 participant C as NPU Compute Stream
 participant N as Network Stream
 C->>C: 启动 本地 KV FA (FA_local)
 N->>N: 异步 AllGather 远端 KV
 N-->>C: AllGather 完成
 C->>C: 远端 chunks 合并为长序列 → FA_remote
 C->>C: LSE(FA_local, FA_remote) 合并输出
```

## Applicable Scenarios

- 基于 Ring Attention 的长序列 DiT 推理
- 通信带宽 < 本地 FA 时长时，掩盖效果最佳
- 主要实例：Wan2.2-I2V 多卡 I2V 推理

## Constraints

- 需要 NPU 支持 compute stream / comm stream 并行（Atlas A2/A3 均支持）
- FP8（perblock）量化 attention 仅支持 Ulysses 序列并行；当 `ring_world_size > 1`（即走 Ring 路径，含 Ring Overlap）时 `module/unified_sp/core.py` 的 `UnifiedSPAttention.__init__` 在 `if fa_perblock_fp8:` 分支直接 `raise ValueError("The quantization method supports only Ulysses Attention sequence parallel now!")`。故 Ring Overlap 不能与 FP8 attention 同开——此为源代码硬约束，非推断
- 依赖 LSE 合并的数值稳定性（合并采用在线 softmax max-LSE 减法重加权，见 Mechanism）

## Known Results

源文档仅定性描述"将通信时间隐藏在本地计算中"，未给出该优化单项的加速比。unverified。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md) Ring Attention Overlap
- 外部参考实现：<https://gitcode.com/weixin_45381022/cann-recipes-infer_wan_overlap/blob/28bf626f6a7db5f1741f37dd0aeb8f90a9bcfde0/module/unified_sp/core.py>

## Links

- [ring-attention](../parallelism/ring_attention.md)
- [ulysses](../parallelism/ulysses.md)
- [wan2.2-i2v](../models/wan2_2_i2v.md)