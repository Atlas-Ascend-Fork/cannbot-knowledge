---
type: Optimization
title: 跨 Prefill/Decode 默认 config 集群规模不一致 + 非默认卡数验证边界
description: 跨 Prefill/Decode 默认 config 集群规模不一致 + 非默认卡数验证边界。把某模型的默认 prefill / decode config 迁到与默认目标不同的卡数上跑（如 32 卡）时，别默认两阶段同规模——默认 prefill 与 decode config 假设的集群规模可能不一致，直接照搬会在其中一个阶段对不上实际集群。
tags:
- task.optimization
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/13
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a3
---

# 跨 Prefill/Decode 默认 config 集群规模不一致 + 非默认卡数验证边界

## 适用场景

把某模型的默认 prefill / decode config 迁到与默认目标不同的卡数上跑（如 32 卡）时，别默认两阶段同规模——默认 prefill 与 decode config 假设的集群规模可能不一致，直接照搬会在其中一个阶段对不上实际集群。

## 规则

- **两阶段默认目标卡数可能相差一倍**：以 [DeepSeek-V3.2-Exp](../../../concepts/models/deepseek_v3_2_exp.md)（Atlas A3）为例，默认 config 的 `world_size` 注释为 `= 2 * chip_num in A3`（world_size = 2 × 卡数）：
  - 默认 prefill config `world_size: 64` → 目标 **32 卡**；
  - 默认 decode config `world_size: 128`、`cp_size: 128` → 目标 **64 卡**。
  即同一模型两阶段默认 config 的目标卡数相差一倍（prefill 32 卡 / decode 64 卡），维护者确认默认 decode config 就是给 64 卡环境用的。
- **迁移时按阶段独立对齐卡数**：`world_size` 设为 `2 × 目标卡数`、`cp_size`（[CP](../../../concepts/parallelism/context_parallel.md)）随 `world_size` 对齐；prefill 与 decode 分别核对，不假设同规模。

## 验证边界（风险告警）

官方只验证过 **64 卡 decode `batch_size=512`** 这一个 decode 数据点，**未验证 32 卡 decode 的 batch_size 上限**——非默认卡数下的 batch_size 无官方背书，须使用者按自身业务与实测确定。迁到非默认卡数时把 batch 上限当作需自测的未知量，不要照搬默认值当上限。

## 边界

无 before→after 数字，本页为跨阶段卡数对齐的部署约定 + 验证边界告警。原 issue 复现者自报的具体 32 卡 decode 参数无维护者背书、无独立复测，不作事实面，仅保留"非默认卡数下 batch 上限须自测"这一可迁移结论。长序列 decode 沿 S 维切 KV Cache 见 [kvp-longseq-decode](../../../guides/experience/interventions/kvp_longseq_decode.md)；长序列 prefill 的 CP 选型见 [long-seq-prefill-context-parallel](long_seq_prefill_context_parallel.md)。

## Evidence

- `config 事实`（clone @2c45117）：prefill 默认 config `world_size: 64`、decode 默认 config `world_size: 128 / cp_size: 128`，两处注释均 `= 2 * chip_num in A3` → prefill 32 卡、decode 64 卡。
- `维护者确认`：默认 decode config = 64 卡；仅验证过 64 卡 decode bs=512、未验证 32 卡 decode batch 上限。
- 溯源下探：[cann-recipes-infer-issue-13-question-32-config](https://gitcode.com/cann/cann-recipes-infer/issues/13)