---
type: API
title: OpAICoreConfig
description: OpAICoreConfig算子配置接口索引。
tags: [task.lookup, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICoreConfig/OpAICoreConfig.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# OpAICoreConfig

OpAICoreConfig 用于定义算子在 AICore 上的编译与执行配置，包括输入输出描述（Input、Output）、动态编译与格式支持标志（DynamicCompileStaticFlag、DynamicFormatFlag）、动态 Shape 与 Rank 支持（DynamicShapeSupportFlag、DynamicRankSupportFlag）、精度降级（PrecisionReduceFlag）和扩展配置信息（ExtendCfgInfo）。通过 REGISTER_OP_AICORE_CONFIG 宏注册。

<!-- cannbot:related:start -->
## 相关

- [AddConfig（OpAICoreDef）](../op_ai_core_def/add_config.md)（`related`）：AddConfig 也消费 OpAICoreConfig，并且同一处理器下优先于 REGISTER_OP_AICORE_CONFIG 覆盖配置；这是必须了解的注册优先级。
- [OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）](../register_op_aicore_config.md)（`related`）：《OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）》的任务是“不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方式，针对不同的AI处理器型号注册差异化的算子原型。REGISTER_OP_AICORE_CONFIG宏在不改变原有注册的基础上，允许单独新增文件来注册算子在不同硬件形态上的差异化信息。 使用该注册宏需要包含以下头文件：”。《OpAICoreConfig》具体提供“OpAICoreConfig算子配置接口索引。”，它直接用于REGISTER_OP_AICORE_CONFIG 与 OpAICoreConfig、AddConfig、OpDef 的注册闭环。
- [OpAICoreDef](../op_ai_core_def/op_ai_core_def.md)（`same_topic`）：OpAICoreDef 与《OpAICoreConfig》的实质衔接是：OpAICoreDef 通过 SetTiling 与 AddConfig 绑定 tiling 和 OpAICoreConfig；注册宏及缺 AddConfig 故障验证这条 SOC 选择契约。
- [Output（原型注册管理）](output.md)（`same_topic`）：Output 是 OpAICoreConfig 对象构建差异化输出签名的具体方法；索引页给出对象其余配置与注册入口。
- [PrecisionReduceFlag](precision_reduce_flag.md)（`same_topic`）：PrecisionReduceFlag 与《OpAICoreConfig》的实质衔接是：PrecisionReduceFlag 是 OpAICoreConfig 字段，只有在该配置对象及 allow_mix_precision 条件下才生效。
<!-- cannbot:related:end -->
