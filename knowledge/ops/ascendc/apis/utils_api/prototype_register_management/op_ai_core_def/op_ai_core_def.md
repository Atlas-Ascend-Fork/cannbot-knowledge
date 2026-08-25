---
type: API
title: OpAICoreDef
description: OpAICoreDef算子定义接口索引。
tags: [task.lookup, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICoreDef/OpAICoreDef.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# OpAICoreDef

OpAICoreDef 用于定义算子在 AICore 上的行为，包括 Tiling 设置（SetTiling）、支持性检查（SetCheckSupport）、格式选择（SetOpSelectFormat）、支持信息（SetOpSupportInfo）、规格信息（SetOpSpecInfo）和参数泛化（SetParamGeneralize）。还提供 AddConfig 添加多档配置和 LaunchWithZeroEleOutputTensors 控制零元素输出的启动行为。

<!-- cannbot:related:start -->
## 相关

- [def.cpp 缺 AddConfig 致 SOC_NOT_SUPPORT](../../../../runbooks/compilation/def_cpp_addconfig_soc_not_support.md)（`exemplifies`）：this->AICore() 注册链属于 OpAICoreDef，该文档界定 AddConfig 所在对象。
- [OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）](../register_op_aicore_config.md)（`related`）：《OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）》的任务是“不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方式，针对不同的AI处理器型号注册差异化的算子原型。REGISTER_OP_AICORE_CONFIG宏在不改变原有注册的基础上，允许单独新增文件来注册算子在不同硬件形态上的差异化信息。 使用该注册宏需要包含以下头文件：”。《OpAICoreDef》具体提供“OpAICoreDef算子定义接口索引。”，它直接用于REGISTER_OP_AICORE_CONFIG 与 OpAICoreConfig、AddConfig、OpDef 的注册闭环。
- [AICore（OpDef）](../op_def/ai_core.md)（`same_topic`）：AICore 返回的 OpAICoreDef 承载 tiling、能力检查与配置方法，是该调用的实际配置对象。
- [AddConfig（OpAICoreDef）](add_config.md)（`same_topic`）：OpAICoreDef 与《AddConfig（OpAICoreDef）》的实质衔接是：OpAICoreDef 通过 SetTiling 与 AddConfig 绑定 tiling 和 OpAICoreConfig；注册宏及缺 AddConfig 故障验证这条 SOC 选择契约。
- [OpAICoreConfig](../op_ai_core_config/op_ai_core_config.md)（`same_topic`）：OpAICoreDef 与《OpAICoreConfig》的实质衔接是：OpAICoreDef 通过 SetTiling 与 AddConfig 绑定 tiling 和 OpAICoreConfig；注册宏及缺 AddConfig 故障验证这条 SOC 选择契约。
- [SetOpSpecInfo](set_op_spec_info.md)（`same_topic`）：SetOpSpecInfo 与《OpAICoreDef》的实质衔接是：SetOpSpecInfo 是 OpAICoreDef 的专用信息配置方法，只有在该定义对象上下文中生效。
- [SetTiling（OpAICoreDef）](set_tiling.md)（`same_topic`）：OpAICoreDef 与《SetTiling（OpAICoreDef）》的实质衔接是：OpAICoreDef 通过 SetTiling 与 AddConfig 绑定 tiling 和 OpAICoreConfig；注册宏及缺 AddConfig 故障验证这条 SOC 选择契约。
<!-- cannbot:related:end -->
