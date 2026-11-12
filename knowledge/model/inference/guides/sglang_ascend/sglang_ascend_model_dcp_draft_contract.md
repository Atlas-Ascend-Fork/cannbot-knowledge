---
type: Guide
title: SGLang 昇腾模型的 DCP 与 draft KV 规划合同
description: 说明 NPU DCP 模型白名单、Kimi-K3 的 A2A 配置和 NextN 执行宽度与 KV 规划的一致性。
tags:
- task.implementation
- topic.parallelism
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/model_hook.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/model_overrides/kimi_k3.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/configs/model_config.py
  role: supporting
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-09T04:35:29Z'
platforms: []
---

# SGLang 昇腾模型的 DCP 与 draft KV 规划合同

## 模型与并行前提

NPU 的 decode-context-parallel-size>1 仅允许 DeepSeek DSA 与 Kimi-K3，其他模型在 model-specific adjustments 中抛 ValueError。DCP 参数的存在不能解释为任意模型可分摊 KV。

Kimi-K3 在 NPU 提前返回之前仍先拒绝 enable_prefill_cp；DCP>1 且 speculative_algorithm=DSPARK 时还要求 SGLANG_RAGGED_VERIFY_MODE=static，compact/cap-accept 等模式会报错。满足这些前置校验后，NPU override 才将 dcp_comm_backend 设为 a2a，并关闭 dcp_replicate_q_proj，然后提前返回，跳过 CUDA cutedsl/trtllm 的专属设置。DSA 的 GPU prefill-CP 参数改写不适用于 NPU，应由 Ascend 分支处理。

## draft 与 KV 容量

`mla_attention_dcp_size` 在 is_nextn 且 NPU 时返回 1：draft attention 使用 allocator-global slots 和非 DCP 执行。KV 规划必须调用同一个函数，不能按 target DCP width 机械缩小 draft cache，否则索引范围与池容量不一致。

配置前确认 target/draft 架构、DCP size 和真实 attention backend；分别核对 KV pool shape、slot 地址和每 rank request 映射。验证多步 decode、speculative verify、idle rank 及相同 batch size 下 positions 改变的情况。DCP 会增加通信与 metadata 成本，回退到 size=1 需重建池和图；本卡没有测得内存或时延收益。
