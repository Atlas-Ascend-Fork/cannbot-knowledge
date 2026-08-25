---
type: API
title: Output（原型注册管理）
description: 某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输出不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子输出。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输出信息。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICoreConfig/Output.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Output

## 功能说明
某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输出不同。
通过该接口，可针对不同的AI处理器型号注册差异化的算子输出。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输出信息。
## 函数原型
## 参数说明
## 返回值说明
算子参数定义，OpParamDef请参考OpParamDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [AddConfig（OpAICoreDef）](../op_ai_core_def/add_config.md)（`related`）：Output 配好 OpAICoreConfig 后由 AddConfig 连同处理器型号注册到 OpAICoreDef，形成配置到生效的链路。
- [Input（原型注册管理）](input.md)（`related`）：Input/Output 分别为特定处理器注册差异化原型参数，并返回 OpParamDef 继续配置；共同定义处理器专属签名。
- [OpAICoreConfig](op_ai_core_config.md)（`same_topic`）：Output 是 OpAICoreConfig 对象构建差异化输出签名的具体方法；索引页给出对象其余配置与注册入口。
<!-- cannbot:related:end -->
