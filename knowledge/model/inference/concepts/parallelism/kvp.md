---
type: Concept
title: KVP（KV Parallelism）：长序列 Decode 的 KV Cache 序列分片与历史状态
description: 当前版本不提供 LongCat KVP 配置或部署入口；撤下旧代码、旧 YAML 和多提交历史配方。
aliases:
- KVP
- KV Parallelism
tags:
- task.design
- topic.parallelism
- topic.attention
- topic.kv_cache
status: deprecated
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py
  role: constraint
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T13:44:43Z'
platforms:
- agnostic
---

# LongCat KVP：当前入口已停用

## 当前状态

当前 LongCat 模型与 ParallelConfig 没有 kvp_size 配置或旧 KVP Attention 分支。本卡停用，不能通过设置 kvp_size=1 或复制旧 YAML 启用 KVP。旧分片代码、LSE 合并配方、耦合约束及历史 commit 对照已从当前知识正文撤下；需要追溯时查看本仓 Git 历史。

## 迁移边界

删除旧键并不自动迁移权重、缓存或请求分布。应选择当前 LongCat 支持的配置，重新核对模型、TP/DP、缓存容量与输出。CP 也不是此模型的直接替代：当前 LongCat check_model_settings 要求 cp_size=1。

## 相关入口

- [当前 LongCat 部署](../../guides/models/longcat_flash_deployment.md)
- [推理配置](../../concepts/techniques/inference_config.md)


## Evidence

- [inference_config.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py)（primary）
- [modeling_longcat_flash.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py)（constraint）
