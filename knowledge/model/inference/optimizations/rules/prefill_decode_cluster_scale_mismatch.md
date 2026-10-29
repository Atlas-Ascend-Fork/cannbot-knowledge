---
type: Optimization
title: 跨 Prefill/Decode 的集群配置核对：区分 rank、阶段与验证范围
description: 以固定 DeepSeek A3 配置为例，分别核对 Prefill/Decode 的 world_size、卡数和阶段门控；配置值与 Issue 回复的已测试数据分开，不将样例 batch 当部署上限。
tags:
- task.optimization
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/fa6892b54681724ac433118b2088ac9b614779f6/models/deepseek-v3.2-exp/config/deepseek_v3.2_exp_rank_64_64ep_prefill.yaml
  role: example
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/fa6892b54681724ac433118b2088ac9b614779f6/models/deepseek-v3.2-exp/config/deepseek_v3.2_exp_rank_128_128ep_decode.yaml
  role: example
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/fa6892b54681724ac433118b2088ac9b614779f6/models/deepseek-v3.2-exp/models/modeling_deepseek.py
  role: implementation
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/fa6892b54681724ac433118b2088ac9b614779f6/models/deepseek-v3.2-exp/infer.py
  role: constraint
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/13
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-20T12:49:18Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - prefill
      - decode
      objective:
      - bringup
---

# 跨 Prefill/Decode 的集群配置核对：区分 rank、阶段与验证范围

## 适用场景

把 Prefill 或 Decode 配置迁到另一集群规模时，分别核对进程/rank 数、卡数、并行组与阶段门控，避免假设两个阶段的样例目标规模相同。本卡覆盖两个阶段的同一核对规则，因此 Scope 的 `phase: [prefill, decode]` 表示二者均可使用；不表示同时执行两阶段或共用一套参数。

## 固定配置示例

以下仅描述 DeepSeek-V3.2-Exp 提交 `fa6892b54681724ac433118b2088ac9b614779f6`，不声称是当前默认值：

| 样例 | world_size | 按样例注释折算的 A3 卡数 | batch_size | cp_size |
|---|---:|---:|---:|---:|
| rank_64_64ep_prefill | 64 | 32 | 64 | 64 |
| rank_128_128ep_decode | 128 | 64 | 256 | 128 |

两个 YAML 的注释将 `world_size` 说明为 A3 的 `2 * chip_num`；这里沿用该样例与 Issue 13 的卡数口径，不能外推所有型号的 rank/物理卡映射。读取目标硬件和进程配置后再换算。

## 阶段门控与迁移

Decode YAML 写有 `cp_size: 128`，但建模的 CP 分支受 Prefill 门控；该值不证明 Decode 进行了序列切分。固定入口启用 CP 时仍校验 `world_size == cp_size`，应同时核对配置合法性与阶段实际执行路径。

迁移时逐项核对实际 rank 数、每层 TP/EP/CP、batch 整除及缓存布局；Prefill 与 Decode 独立完成检查。不要把两个阶段的卡数比例或某个 `cp_size` 值作为通用部署规则。

## 已测试数据与未知范围

Issue 13 的回复报告默认 Decode 面向 64 卡、测试过 64 卡 Decode `batch_size=512`，未验证 32 卡 Decode batch 上限。这是讨论当时的自报范围，与上表固定 YAML 的 `batch_size=256` 是不同证据；两者都不能作为硬件容量上限。

本次未运行模型或验证非默认规模。迁移前保存配置、版本与输出基线，先检查合法性，再按目标工作负载测量显存峰值、输出、TTFT/Decode 时延和波动；不通过时恢复原配置并重新核对组与缓存，不能仅凭启动成功验收。

## 相关入口

- [长序列 Prefill CP 决策](long_seq_prefill_context_parallel.md)
- [KVP 历史机制与撤回状态](../../concepts/parallelism/kvp.md)：旧 Guide 已停用，不作为当前部署建议。

## Evidence

固定 YAML、入口和建模源码分别支撑配置值、校验与阶段行为；Issue 13 只支撑当时报告的测试范围，没有独立复测或新增 `verified`。
