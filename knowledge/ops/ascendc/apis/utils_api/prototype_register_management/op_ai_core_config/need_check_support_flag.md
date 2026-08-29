---
type: API
title: NeedCheckSupportFlag
description: 标识是否在算子融合阶段调用算子参数校验函数进行data type与shape的校验。 - 若配置为"true"，框架会调用通过SetCheckSupport设置的算子参数校验函数，检查算子是否支持指定输入，此场景下需要自行实现算子参数校验的回调函数。
  - 若配置为"false"，表示不需要进行校验。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICoreConfig/NeedCheckSupportFlag.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# NeedCheckSupportFlag

## 功能说明
标识是否在算子融合阶段调用算子参数校验函数进行data type与shape的校验。
-   若配置为"true"，框架会调用通过SetCheckSupport设置的算子参数校验函数，检查算子是否支持指定输入，此场景下需要自行实现算子参数校验的回调函数。
-   若配置为"false"，表示不需要进行校验。
## 函数原型
## 参数说明
## 返回值说明
OpAICoreConfig类，请参考OpAICoreConfig。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [SetCheckSupport](../op_ai_core_def/set_check_support.md)（`related`）：SetCheckSupport 卡要求“需要将NeedCheckSupportFlag参数配置为true”；NeedCheckSupportFlag 卡说明“框架会调用通过SetCheckSupport设置的算子参数校验函数”。回调注册和调用开关是融合阶段支持性校验的共同条件。
<!-- cannbot:related:end -->
