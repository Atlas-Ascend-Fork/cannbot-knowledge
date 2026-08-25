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

- [算子原型定义](../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/operator_prototype_definition.md)（`explains`）：指南通过 AICore 关联 TilingFunc 与 AI Core 配置，把外部接口描述接到执行实现。
- [AddConfig（OpAICoreDef）](../op_ai_core_def/add_config.md)（`related`）：AddConfig 追加具体 SoC 与实现配置，把抽象 AICore 定义落到可用后端组合。
- [OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）](../register_op_aicore_config.md)（`related`）：《OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）》的任务是“不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方式，针对不同的AI处理器型号注册差异化的算子原型。REGISTER_OP_AICORE_CONFIG宏在不改变原有注册的基础上，允许单独新增文件来注册算子在不同硬件形态上的差异化信息。 使用该注册宏需要包含以下头文件：”。《AICore（OpDef）》具体提供“设置AICore的配置信息：包括Tiling处理回调函数、能力检查回调函数、基础的配置信息等。”，它直接用于REGISTER_OP_AICORE_CONFIG 与 OpAICoreConfig、AddConfig、OpDef 的注册闭环。
- [SetCheckSupport](../op_ai_core_def/set_check_support.md)（`related`）：SetCheckSupport 为 AICore 配置能力检查回调，决定当前输入规格是否可走 AI Core。
- [SetTiling（OpAICoreDef）](../op_ai_core_def/set_tiling.md)（`related`）：SetTiling 把 Host tiling 回调挂到 AICore 配置，是 AICore 描述中的核心后续动作。
- [原型注册接口（OP_ADD）](../op_add.md)（`related`）：《原型注册接口（OP_ADD）》处理“注册算子的原型定义，从而确保算子能够被框架正确识别、编译和执行。 算子原型主要描述了算子的输入输出、属性等信息以及算子在AI处理器上相关实现信息，并关联tiling实现等函数。算子原型通过自定义的算子类来承载，该算子类继承自OpDef类。完成算子的原型定义等操作后，需要调用OP_ADD接口，传入算子类型（自定义算子类的类名），进行算子原型注册。详细内容请参考算子原型定义。”。《AICore（OpDef）》明确提供“设置AICore的配置信息：包括Tiling处理回调函数、能力检查回调函数、基础的配置信息等。”，其参数、调用或验证步骤直接接入OP_ADD 宏与 OpDef、注册函数、原型库和注册故障的可执行闭环。
- [OpAICoreDef](../op_ai_core_def/op_ai_core_def.md)（`same_topic`）：AICore 返回的 OpAICoreDef 承载 tiling、能力检查与配置方法，是该调用的实际配置对象。
<!-- cannbot:related:end -->
