---
type: API
title: SetCheckSupport
description: 如果您需要在算子融合阶段进行算子参数校验，则可实现算子参数校验回调函数，并通过该接口进行注册。同时，需要将NeedCheckSupportFlag参数配置为true，则算子编译和融合阶段会调用注册的算子参数校验函数进行相关信息的校验。
  若算子参数校验函数校验通过，则代表AI Core支持此算子参数，会选择AI Core上相应的算子执行；否则，会继续查询AI CPU算子库然后执行。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICoreDef/SetCheckSupport.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# SetCheckSupport

## 功能说明
如果您需要在算子融合阶段进行算子参数校验，则可实现算子参数校验回调函数，并通过该接口进行注册。同时，需要将NeedCheckSupportFlag参数配置为true，则算子编译和融合阶段会调用注册的算子参数校验函数进行相关信息的校验。
若算子参数校验函数校验通过，则代表AI Core支持此算子参数，会选择AI Core上相应的算子执行；否则，会继续查询AI CPU算子库然后执行。
## 函数原型
## 参数说明
## 返回值说明
OpAICoreDef请参考OpAICoreDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [AICore（OpDef）](../op_def/ai_core.md)（`related`）：SetCheckSupport 为 AICore 配置能力检查回调，决定当前输入规格是否可走 AI Core。
- [NeedCheckSupportFlag](../op_ai_core_config/need_check_support_flag.md)（`related`）：NeedCheckSupportFlag=true 只会在已通过 SetCheckSupport 注册回调时触发 dtype/shape 校验；二者必须配套。
<!-- cannbot:related:end -->
