---
type: Guide
title: 已停用：LongCat A3 长序列 KVP 的历史条件与配置
description: 保留回退前 LongCat A3 KVP 的分片条件、校验与测试样例；PR501 及 2c45117 按键存在性拒绝 kvp_size，设为 1 也不可用，本 Guide 不再提供当前部署建议。
tags:
- task.debugging
- topic.attention
- topic.kv_cache
- topic.speculative_decoding
status: deprecated
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/de084d3cc7fbf0117f38c6b0a63936fd9991e415/models/longcat-flash/models/modeling_longcat_flash.py
  role: implementation
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/de084d3cc7fbf0117f38c6b0a63936fd9991e415/models/longcat-flash/config/longcat_flash_densetp8_ep32_kvp8_gegraph_w8a8.yaml
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/d6ba03b342efe7eecb814cb4657242e28894093a/models/longcat-flash/models/model_setting.py
  role: constraint
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/d6ba03b342efe7eecb814cb4657242e28894093a/executor/utils/common_utils.py
  role: constraint
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/152ad5ef50d3dee75b9c18e6c4766814e19eb1f5/models/longcat-flash/models/model_setting.py
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat-flash/models/model_setting.py
  role: constraint
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-21T01:48:04Z'
platforms:
- a3
---

# 已停用：LongCat A3 长序列 KVP 的历史条件与配置

## 停用原因与版本边界

本页保留迁移后的历史入口供历史引用，不再提供当前部署建议。[PR501](https://gitcode.com/cann/cann-recipes-infer/merge_requests/501) 于 2026-05-29 合入撤回；固定提交 `152ad5ef50d3dee75b9c18e6c4766814e19eb1f5` 及 `2c45117d781ab9ab88dcb89a28ae30f5d2450399` 均在 `parallel_config` 包含 `kvp_size` 键时抛出 `kvp_size is removed; longcat KVP is temporarily disabled`。

**在这两个版本中，`kvp_size: 1` 也会触发守卫。** 旧版“设为 1 关闭”的回退步骤不能用于这些版本。对这些校验入口，应先移除旧配置键并核对对应版本的非 KVP 配置与模型路径；移除键不代表已有 KVP 权重、缓存或运行态可以直接复用。本次未验证配置迁移，不绕过守卫。

没有已核验的当前替代部署方案，因此不设置 `replaced_by`。机制解释见 [KVP Concept](../../concepts/parallelism/kvp.md)。后续版本是否恢复支持，需要另行核验。

## 回退前的适用条件

以下内容仅对应 LongCat-Flash / Atlas A3 在 `de084d3cc7fbf0117f38c6b0a63936fd9991e415` 与 `d6ba03b342efe7eecb814cb4657242e28894093a` 的历史实现：长序列 Decode 的 KV Cache 显存或访存压力较大，组内 rank 共享同一批请求、分别持有序列维 KV 分片。Prefill 也参与分片 KV 写入与相应 head 切分，不能表述为“Prefill 不适用 KVP”。长序列 Prefill 的优化选择另见 [CP 规则](../../optimizations/rules/long_seq_prefill_context_parallel.md)。

Decode 通过局部 Attention、两次 head 维 AllToAll 和内联 LSE softmax 加权合并恢复输出；随后 o_proj 在 KVP 组内 AllReduce。固定源码使用内联归约，不应因旧文档的算子名而额外寻找 `npu_attention_update`。具体机制只维护在 Concept。

## 历史配置的耦合校验

`kvp_size > 1` 时，回退前校验要求：

| 条件 | 对应边界 |
|---|---|
| `world_size % kvp_size == 0` | KVP 组完整划分；公共并行校验覆盖 `kvp_size` |
| `o_proj_tp_size == kvp_size` | 输出投影与 KVP 组宽度一致 |
| `attn_tp_size == 1` | 该 KVP 路径不叠加 Attention TP |
| `cp_size == 1` | 该实现不同时启用 CP |
| `batch_size % (world_size // kvp_size) == 0` | batch 对组外 DP 维整除 |
| `next_n == 0` | 当时不支持与 MTP 同用 |

这些是固定实现的条件，不是其他模型的通用并行约束，也不构成撤回后可用性证明。

## 历史样例与失败信号

回退前 YAML 使用 `world_size=32`、`kvp_size=8`、`o_proj_tp_size=8`、`attn_tp_size=1`、`batch_size=4`。但该文件同时设置 `decode_only: True`，注释明确只用于 TPOT 测试并影响精度，因此不能作为完整推理的正确性配方。

历史版本违反条件时会报告 `when kvp_size > 1` 下的 Attention TP、o_proj TP、CP 或 batch 整除错误，MTP 则报告 `currently only support next_n = 0`。撤回版本在入口直接报 `kvp_size is removed`，此时不能继续按历史表调参尝试启用。

## 证据与验证边界

- [历史模型源码](https://gitcode.com/cann/cann-recipes-infer/blob/de084d3cc7fbf0117f38c6b0a63936fd9991e415/models/longcat-flash/models/modeling_longcat_flash.py)与[测试配置](https://gitcode.com/cann/cann-recipes-infer/blob/de084d3cc7fbf0117f38c6b0a63936fd9991e415/models/longcat-flash/config/longcat_flash_densetp8_ep32_kvp8_gegraph_w8a8.yaml)：核对分片、通信、样例与精度限制。
- [历史模型校验](https://gitcode.com/cann/cann-recipes-infer/blob/d6ba03b342efe7eecb814cb4657242e28894093a/models/longcat-flash/models/model_setting.py)和[公共校验](https://gitcode.com/cann/cann-recipes-infer/blob/d6ba03b342efe7eecb814cb4657242e28894093a/executor/utils/common_utils.py)：核对耦合条件。
- [撤回后的入口](https://gitcode.com/cann/cann-recipes-infer/blob/152ad5ef50d3dee75b9c18e6c4766814e19eb1f5/models/longcat-flash/models/model_setting.py)及[引用版本入口](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat-flash/models/model_setting.py)：核对按键存在性拒绝旧配置。

本次未运行模型，没有验证当前启用、迁移、正确性或收益；没有独立 before/after 数据。历史条件保留用于理解与排查，不再作为默认检索的部署建议。
