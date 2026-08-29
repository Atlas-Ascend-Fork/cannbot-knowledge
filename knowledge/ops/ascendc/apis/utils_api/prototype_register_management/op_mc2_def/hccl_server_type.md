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

<!-- cannbot:related:start -->
## 相关

- [OpMC2Def简介](op_mc2_def_intro.md)（`related`）：“使用该接口前，算子需要先通过MC2接口注册该算子是通算融合算子，注册后即返回一个OpMC2Def结构。”与“OpMC2Def类用于在Host侧配置通算融合算子的通信域名称，是通算融合算子原型注册管理的重要组成部分。”分别来自双方当前正文。HcclServerType 明确要求先取得 OpMC2Def，概览卡解释该对象负责 Host 侧通信域配置，因此两卡连接 MC2 注册结果与服务端类型配置步骤。
<!-- cannbot:related:end -->
