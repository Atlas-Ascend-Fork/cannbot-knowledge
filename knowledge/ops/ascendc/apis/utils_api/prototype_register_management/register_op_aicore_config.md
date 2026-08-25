---
type: API
title: OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）
description: 不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方式，针对不同的AI处理器型号注册差异化的算子原型。REGISTER_OP_AICORE_CONFIG宏在不改变原有注册的基础上，允许单独新增文件来注册算子在不同硬件形态上的差异化信息。
  使用该注册宏需要包含以下头文件：
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/REGISTER_OP_AICORE_CONFIG.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）

## 功能说明
不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方式，针对不同的AI处理器型号注册差异化的算子原型。REGISTER_OP_AICORE_CONFIG宏在不改变原有注册的基础上，允许单独新增文件来注册算子在不同硬件形态上的差异化信息。
使用该注册宏需要包含以下头文件：
## 函数原型
## 参数说明
## 返回值说明
无
## 约束说明
若算子同时使用AddConfig注册算子支持的AI处理器型号以及OpAICoreConfig信息，且AI处理器型号相同时，通过AddConfig方式注册的配置优先级更高，会覆盖REGISTER_OP_AICORE_CONFIG宏注册的OpAICoreConfig信息。
