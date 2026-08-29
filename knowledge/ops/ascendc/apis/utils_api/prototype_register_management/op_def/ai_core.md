---
type: API
title: AICore（OpDef）
description: 设置AICore的配置信息：包括Tiling处理回调函数、能力检查回调函数、基础的配置信息等。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/AICore.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# AICore

## 功能说明
设置AICore的配置信息：包括Tiling处理回调函数、能力检查回调函数、基础的配置信息等。
## 函数原型
## 参数说明
无
## 返回值说明
OpAICoreDef请参考OpAICoreDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [ACLNN 161001 — ascend910_93 缺算子内核配置](../../../../runbooks/compilation/aclnn_161001_ascend910_93.md)（`exemplifies`）：在 `*_def.cpp` 的 `AICore()` 链上, 为目标设备会上报的**每个** socVersion 显式 `.AddConfig("<soc>")` (参考 hardSwish8 同时 `.AddConfig("ascend910b").AddConfig("ascend910_93")` 的写法)。；设置AICore的配置信息：包括Tiling处理回调函数、能力检查回调函数、基础的配置信息等。。Runbook 的修复在 OpDef 的 AICore 链上为每个设备 socVersion 添加配置，AICore API 卡定义该对象承载基础配置及回调信息，因此 161001 配置缺失是该 API 配置职责的具体故障实例。
<!-- cannbot:related:end -->
