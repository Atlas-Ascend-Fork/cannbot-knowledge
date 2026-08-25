---
type: API
title: MC2（OpDef）
description: 注册该算子是通算融合算子，调用该接口后会返回一个OpMC2Def结构，后续可通过该结构配置通信域名称。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/MC2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# MC2

## 功能说明
注册该算子是通算融合算子，调用该接口后会返回一个OpMC2Def结构，后续可通过该结构配置通信域名称。
## 函数原型
## 参数说明
无
## 返回值说明
OpMC2Def结构，后续可通过该结构配置通信域名称。
## 约束说明
基于旧版本CANN包（不支持MC2特性）生成的自定义算子工程，无法兼容MC2接口。在使用非当前版本CANN包生成的自定义算子工程时，需特别注意兼容性问题。您可以通过查看自定义算子工程下cmake/util/ascendc_impl_build.py中有无_build_mc2_ctx字段来确认当前工程是否支持该特性，如果未找到该字段，则需要重新生成自定义算子工程以启用MC2特性。

<!-- cannbot:related:start -->
## 相关

- [MC²算子性能调优案例](../../../../guides/operator_practice/best_practices/mc_operator_tuning.md)（`explains`）：《MC²算子性能调优案例》的任务是“MC2通算融合算子性能调优案例，通过数据切分实现计算与通信流水掩盖，介绍切分策略制定与优化方法。”。《MC2（OpDef）》具体提供“注册该算子是通算融合算子，调用该接口后会返回一个OpMC2Def结构，后续可通过该结构配置通信域名称。”，它直接用于MC2 通算融合的 Matmul 性能入口和 MC2 原型配置。
- [HcclServerType](../op_mc2_def/hccl_server_type.md)（`related`）：HcclServerType 与《MC2（OpDef）》的实质衔接是：HcclServerType 是 OpMC2Def 注册中的 server 枚举；构造、HcclGroup 和 MC2 OpDef 共同决定 MC2 原型如何声明通信域与服务端角色。
- [HcclGroup（OpMC2Def）](../op_mc2_def/hccl_group.md)（`same_topic`）：HcclGroup 是 MC2 返回对象上的直接后续配置，用于绑定通算融合的通信域名称。
- [OpMC2Def](../op_mc2_def/op_mc2_def.md)（`same_topic`）：MC2 返回 OpMC2Def，后续通信域配置都在该对象上完成。
- [OpMC2Def构造函数](../op_mc2_def/op_mc2_def_constructor.md)（`same_topic`）：OpDef::MC2 创建并挂接该对象，连接普通 OpDef 与 MC2 扩展定义。
- [OpMC2Def简介](../op_mc2_def/op_mc2_def_intro.md)（`same_topic`）：OpMC2Def简介 与《MC2（OpDef）》的实质衔接是：OpMC2Def 在 host 原型侧声明 HcclGroup 与 HcclServerType，构造后把通信域映射为核侧 HCCL Context；MC2 OpDef 是其注册入口。
<!-- cannbot:related:end -->
