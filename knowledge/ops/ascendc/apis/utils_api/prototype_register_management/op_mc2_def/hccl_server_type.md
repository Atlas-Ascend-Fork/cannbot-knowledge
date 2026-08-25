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

- [MC2（OpDef）](../op_def/mc2.md)（`related`）：HcclServerType 与《MC2（OpDef）》的实质衔接是：HcclServerType 是 OpMC2Def 注册中的 server 枚举；构造、HcclGroup 和 MC2 OpDef 共同决定 MC2 原型如何声明通信域与服务端角色。
- [HcclGroup（OpMC2Def）](hccl_group.md)（`same_topic`）：HcclServerType 与《HcclGroup（OpMC2Def）》的实质衔接是：HcclServerType 是 OpMC2Def 注册中的 server 枚举；构造、HcclGroup 和 MC2 OpDef 共同决定 MC2 原型如何声明通信域与服务端角色。
- [OpMC2Def](op_mc2_def.md)（`same_topic`）：HcclServerType 与《OpMC2Def》的实质衔接是：HcclServerType 是 OpMC2Def 注册中的 server 枚举；构造、HcclGroup 和 MC2 OpDef 共同决定 MC2 原型如何声明通信域与服务端角色。
- [OpMC2Def构造函数](op_mc2_def_constructor.md)（`same_topic`）：HcclServerType 与《OpMC2Def构造函数》的实质衔接是：HcclServerType 是 OpMC2Def 注册中的 server 枚举；构造、HcclGroup 和 MC2 OpDef 共同决定 MC2 原型如何声明通信域与服务端角色。
- [OpMC2Def简介](op_mc2_def_intro.md)（`same_topic`）：OpMC2Def简介 与《HcclServerType》的实质衔接是：OpMC2Def 在 host 原型侧声明 HcclGroup 与 HcclServerType，构造后把通信域映射为核侧 HCCL Context；MC2 OpDef 是其注册入口。
<!-- cannbot:related:end -->
