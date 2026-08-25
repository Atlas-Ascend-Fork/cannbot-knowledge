---
type: API
title: AddConfig（OpAICoreDef）
description: 注册算子支持的AI处理器型号以及OpAICoreConfig信息。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICoreDef/AddConfig.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# AddConfig

## 功能说明
注册算子支持的AI处理器型号以及OpAICoreConfig信息。
## 函数原型
## 参数说明
## 返回值说明
无
## 约束说明
不传入aicore_config参数时，对OpAICoreConfig结构中的部分参数会配置成默认值，具体的参数和默认值如下表所示：
不传入aicore_config参数时，OpAICoreConfig默认配置

<!-- cannbot:related:start -->
## 相关

- [def.cpp 缺 AddConfig 致 SOC_NOT_SUPPORT](../../../../runbooks/compilation/def_cpp_addconfig_soc_not_support.md)（`exemplifies`）：根因是 def.cpp 的 AICore().AddConfig 列表缺目标 SOC；AddConfig 定义将 SoC 与 OpAICoreConfig 绑定。
- [AICore（OpDef）](../op_def/ai_core.md)（`related`）：AddConfig 追加具体 SoC 与实现配置，把抽象 AICore 定义落到可用后端组合。
- [OpAICoreConfig](../op_ai_core_config/op_ai_core_config.md)（`related`）：AddConfig 也消费 OpAICoreConfig，并且同一处理器下优先于 REGISTER_OP_AICORE_CONFIG 覆盖配置；这是必须了解的注册优先级。
- [OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）](../register_op_aicore_config.md)（`related`）：《OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）》的任务是“不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方式，针对不同的AI处理器型号注册差异化的算子原型。REGISTER_OP_AICORE_CONFIG宏在不改变原有注册的基础上，允许单独新增文件来注册算子在不同硬件形态上的差异化信息。 使用该注册宏需要包含以下头文件：”。《AddConfig（OpAICoreDef）》具体提供“注册算子支持的AI处理器型号以及OpAICoreConfig信息。”，它直接用于REGISTER_OP_AICORE_CONFIG 与 OpAICoreConfig、AddConfig、OpDef 的注册闭环。
- [Output（原型注册管理）](../op_ai_core_config/output.md)（`related`）：Output 配好 OpAICoreConfig 后由 AddConfig 连同处理器型号注册到 OpAICoreDef，形成配置到生效的链路。
- [OpAICoreConfig构造函数](../op_ai_core_config/op_ai_core_config_constructor.md)（`same_topic`）：OpAICoreConfig构造函数 与《AddConfig（OpAICoreDef）》的实质衔接是：OpAICoreConfig 构造后配置动态能力、输入输出、tiling/support，并注册到 OpAICoreDef。
- [OpAICoreDef](op_ai_core_def.md)（`same_topic`）：OpAICoreDef 与《AddConfig（OpAICoreDef）》的实质衔接是：OpAICoreDef 通过 SetTiling 与 AddConfig 绑定 tiling 和 OpAICoreConfig；注册宏及缺 AddConfig 故障验证这条 SOC 选择契约。
<!-- cannbot:related:end -->
