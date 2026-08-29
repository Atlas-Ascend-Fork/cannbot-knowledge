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

- [HcclGroup（OpMC2Def）](../op_mc2_def/hccl_group.md)（`related`）：HcclGroup 规定“使用该接口前，算子需要先通过MC2接口注册该算子是通算融合算子，注册后即返回一个OpMC2Def结构。”；MC2 页说明“调用该接口后会返回一个OpMC2Def结构，后续可通过该结构配置通信域名称。”，构成 MC2 注册到 HcclGroup 配置的强制调用顺序。
- [OpMC2Def](../op_mc2_def/op_mc2_def.md)（`same_topic`）：“OpMC2Def 用于定义算子在 MC2（多机多卡通信）场景下的执行属性”说明结构体职责，“注册该算子是通算融合算子，调用该接口后会返回一个OpMC2Def结构”说明从 OpDef 进入该结构的注册入口。
<!-- cannbot:related:end -->
