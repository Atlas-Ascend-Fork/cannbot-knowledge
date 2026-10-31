---
type: Optimization
title: Kimi K3：投机验证后按接受长度提交 ReplaySSM 状态
description: 在 950 Kimi K3 Decode/DSpark 路径中，以 checkpoint 与 replay 数据替代逐候选完整状态快照，并保留明确的开关、形状及回退条件。
tags:
- task.optimization
- topic.speculative_decoding
- topic.memory
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/kimi_k3/kimi_k3_inference_guide.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k3/models/modules/attention_data.py
  role: implementation
created_at: '2026-10-29T04:09:03Z'
updated_at: '2026-10-29T15:07:06Z'
platforms:
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      objective:
      - memory
      phase:
      - decode
---

# Kimi K3：投机验证后按接受长度提交 ReplaySSM 状态

## 适用场景与问题信号

适用于固定来源中的 950 Kimi K3 Decode/DSpark 验证路径。逐候选保存完整 KDA 状态会增加状态存储和搬运；拒绝草稿后若直接沿用最后一次验证状态，还会把未接受 token 带入下一步。

## 优化规则与机制

保留每个请求的可提交 checkpoint，并为验证宽度内的候选保存 replay 数据。验证结束后由 Commit 算子仅提交已接受 token 的状态。它改变状态恢复方式，仍须维护请求、接受长度、卷积状态和递推矩阵之间的一致性。

当前文档要求 DSpark、next_n=7、本地 batch≤16、local KDA heads=6、hidden size=7168、head dim=128、ShortConv kernel=4 及 full-rank output gate，并同时具备 ReplaySSM 主算子与 Commit 算子。不能只打开开关而忽略形状或外部算子包。

## 实施、代价与回退

enable_mega_kda 和 enable_mega_kda_replayssm 同时启用时使用 ReplaySSM。关闭 ReplaySSM、保留 MegaKDA 时回到 MegaKDA snapshot；将 enable_mega_kda 和 enable_mega_kda_replayssm 均设为 False 时，使用 fused recurrent snapshot；仅关闭 MegaKDA 而保留 ReplaySSM 会在开关校验阶段抛出 ValueError。Prefill 始终使用 FlashKDA。Commit stream 与主 Decode stream 之间按生产者和消费者关系记录、等待事件。

收益来源是减少完整 snapshot 的保存；代价是 replay 缓冲、提交计算和同步。收益没有独立消融数字，不能把整套 Kimi K3 的加速都归因于此项。

## 验证方法与失效边界

比较三条状态路径在相同输入和接受长度下的输出与后续状态，覆盖全接受、部分接受、拒绝、请求重排及 batch 边界。核对两种 recurrent state 布局和 replay_u/replay_k/replay_decay 的验证宽度。切换路径、形状或权重布局后重新准备编译缓存。缺少兼容算子或形状不满足时使用 snapshot 回退并复验。

## 相关经验与 Evidence

结构见 [Kimi K3](../../concepts/models/kimi_k3.md)。本卡依据固定 README 和技术文档蒸馏，未执行 NPU 测试。
