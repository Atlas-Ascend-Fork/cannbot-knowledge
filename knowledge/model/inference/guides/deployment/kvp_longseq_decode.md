---
type: Guide
title: 已停用：LongCat A3 长序列 KVP 的历史条件与配置
description: 当前版本不提供 LongCat KVP 配置或部署入口；撤下旧代码、旧 YAML 和多提交历史配方。
tags:
- task.debugging
- topic.attention
- topic.kv_cache
- topic.speculative_decoding
status: deprecated
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py
  role: constraint
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T13:44:43Z'
platforms:
- a3
---

# LongCat KVP 部署已停用

## 当前状态

当前仓库没有可运行的 LongCat KVP recipe，ParallelConfig 与模型均不提供 kvp_size。旧 YAML、MTP/CP 耦合表和多版本源码链接不再作为当前部署建议。

## 后续处理

按[当前 LongCat 部署](../models/longcat_flash_deployment.md)选择实际支持的配置，重新核对权重与缓存。删除旧键不代表迁移完成；不绕过配置校验，不将 CP 或 KV offload 自动当作同模型替代。未验证新的 KVP 实现，因此不设置替代 Concept。


## Evidence

- [inference_config.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py)（primary）
- [modeling_longcat_flash.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py)（constraint）
