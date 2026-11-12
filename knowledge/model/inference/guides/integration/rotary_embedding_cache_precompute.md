---
type: Guide
title: RoPE 接入：预计算 cos/sin、按 position_ids 索引与跨层复用
description: RoPE 每层或每步重复计算 cos/sin 时，预计算位置表并缓存、跨层复用；按 position_ids 和 dtype 索引，保留 YaRN、interleaved 与动态 scaling 边界。
tags:
- task.implementation
- topic.attention
- topic.graph_execution
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/rotary-embedding-pattern.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/models/modeling_qwen3_moe.py
  role: supporting
created_at: '2026-11-09T09:23:47Z'
updated_at: '2026-11-10T01:14:22Z'
platforms:
- agnostic
aliases:
- RoPE 缓存
- RoPE 重复计算
- cos sin 预计算
---

# RoPE 接入：预计算 cos/sin、按 position_ids 索引与跨层复用

## 适用范围与机制

用于移植采用固定频率 RoPE 的 Decoder，减少每层或每步重建频率表的 host/设备开销，并稳定编图路径。初始化时按模型 rope_theta、旋转维度、最大位置及 rope scaling 构造 inv_freq/cos_cached/sin_cached，作为不随 checkpoint 保存的 buffer（persistent=False）。forward 按 position_ids 选行，转换到当前 hidden_states dtype，在同一前向中传给需要相同编码的各层。

packed batch 的 position_ids 是每请求的位置，不能用全批 token 偏移代替；Decode 从缓存历史长度对应的位置取值，不能每步从零开始。预计算表覆盖实际最大位置，并与当前设备、模型 dtype 和 scaling 参数一致，超范围时走模型支持的扩容或明确拒绝。

## 模型差异与验证

half-split 与 interleaved 不能互换；局部旋转维、YaRN、mscale_all_dim、长上下文动态 scaling、混合层可能不共享同一张表。先按模型定义保留语义，再选择 npu_rotary_mul 等融合接口；这里的缓存模式不证明任意具体算子支持该编码。

用非零位置、长上下文、不等长 batch 及 Prefill→Decode 对比原始旋转结果，核对 cos/sin dtype、广播轴、仅旋转的子维及 FA 缩放。图模式确认 forward 内没有新增频率表、设备搬运或数据相关 Python 分支。回退原模型的 RoPE 实现并恢复匹配缓存，不能仅以首 token 正确认定改造成功。

相关：[interleaved RoPE 选择](../../runbooks/precision/interleaved_rope_npu_op_selection.md)、[Attention 链路](attention_fusion_chain_selection.md)。

## Evidence

- [.agents/skills/model-infer-fusion/references/rotary-embedding-pattern.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/rotary-embedding-pattern.md)
- [models/qwen3_moe/models/modeling_qwen3_moe.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/models/modeling_qwen3_moe.py)
