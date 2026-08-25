---
type: API
title: HcclServerType
description: 配置HCCL的服务端类型。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpMC2Def/HcclServerType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# HcclServerType

## 功能说明
配置HCCL的服务端类型。
## 函数原型
## 参数说明
## 约束说明
-   使用该接口前，算子需要先通过MC2接口注册该算子是通算融合算子，注册后即返回一个OpMC2Def结构。
-   同时为特定AI处理器型号和所有AI处理器型号配置服务端类型时，特定AI处理器型号配置的优先级更高。
