---
type: API
title: OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）
description: 不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方式，针对不同的AI处理器型号注册差异化的算子原型。REGISTER_OP_AICORE_CONFIG宏在不改变原有注册的基础上，允许单独新增文件来注册算子在不同硬件形态上的差异化信息。
  使用该注册宏需要包含以下头文件：
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/REGISTER_OP_AICORE_CONFIG.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）

## 功能说明
不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方式，针对不同的AI处理器型号注册差异化的算子原型。REGISTER_OP_AICORE_CONFIG宏在不改变原有注册的基础上，允许单独新增文件来注册算子在不同硬件形态上的差异化信息。
使用该注册宏需要包含以下头文件：
## 函数原型
## 参数说明
## 返回值说明
无
## 约束说明
若算子同时使用AddConfig注册算子支持的AI处理器型号以及OpAICoreConfig信息，且AI处理器型号相同时，通过AddConfig方式注册的配置优先级更高，会覆盖REGISTER_OP_AICORE_CONFIG宏注册的OpAICoreConfig信息。

<!-- cannbot:related:start -->
## 相关

- [def.cpp 缺 AddConfig 致 SOC_NOT_SUPPORT](../../../runbooks/compilation/def_cpp_addconfig_soc_not_support.md)（`exemplifies`）：《OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）》的任务是“不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方式，针对不同的AI处理器型号注册差异化的算子原型。REGISTER_OP_AICORE_CONFIG宏在不改变原有注册的基础上，允许单独新增文件来注册算子在不同硬件形态上的差异化信息。 使用该注册宏需要包含以下头文件：”。《def.cpp 缺 AddConfig 致 SOC_NOT_SUPPORT》具体提供“ops-math def.cpp 的 AICore().AddConfig 列表漏 ascend950，build 不生成该 SOC ops-info（aic-ascend950-ops-info.ini 0 字节），TTK 运行时报 SOC_NOT_SUPPORT；判别：SOC_NOT_SUPPORT + 0 字节 ops-info.ini 即指向 def.cpp AddConfig 遗漏，先查 def.cpp 注册块而非 kernel。”，它直接用于REGISTER_OP_AICORE_CONFIG 与 OpAICoreConfig、AddConfig、OpDef 的注册闭环。
- [AICore（OpDef）](op_def/ai_core.md)（`related`）：《OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）》的任务是“不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方式，针对不同的AI处理器型号注册差异化的算子原型。REGISTER_OP_AICORE_CONFIG宏在不改变原有注册的基础上，允许单独新增文件来注册算子在不同硬件形态上的差异化信息。 使用该注册宏需要包含以下头文件：”。《AICore（OpDef）》具体提供“设置AICore的配置信息：包括Tiling处理回调函数、能力检查回调函数、基础的配置信息等。”，它直接用于REGISTER_OP_AICORE_CONFIG 与 OpAICoreConfig、AddConfig、OpDef 的注册闭环。
- [AddConfig（OpAICoreDef）](op_ai_core_def/add_config.md)（`related`）：《OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）》的任务是“不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方式，针对不同的AI处理器型号注册差异化的算子原型。REGISTER_OP_AICORE_CONFIG宏在不改变原有注册的基础上，允许单独新增文件来注册算子在不同硬件形态上的差异化信息。 使用该注册宏需要包含以下头文件：”。《AddConfig（OpAICoreDef）》具体提供“注册算子支持的AI处理器型号以及OpAICoreConfig信息。”，它直接用于REGISTER_OP_AICORE_CONFIG 与 OpAICoreConfig、AddConfig、OpDef 的注册闭环。
- [OpAICoreConfig](op_ai_core_config/op_ai_core_config.md)（`related`）：《OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）》的任务是“不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方式，针对不同的AI处理器型号注册差异化的算子原型。REGISTER_OP_AICORE_CONFIG宏在不改变原有注册的基础上，允许单独新增文件来注册算子在不同硬件形态上的差异化信息。 使用该注册宏需要包含以下头文件：”。《OpAICoreConfig》具体提供“OpAICoreConfig算子配置接口索引。”，它直接用于REGISTER_OP_AICORE_CONFIG 与 OpAICoreConfig、AddConfig、OpDef 的注册闭环。
- [OpAICoreConfig构造函数](op_ai_core_config/op_ai_core_config_constructor.md)（`related`）：《OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）》的任务是“不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方式，针对不同的AI处理器型号注册差异化的算子原型。REGISTER_OP_AICORE_CONFIG宏在不改变原有注册的基础上，允许单独新增文件来注册算子在不同硬件形态上的差异化信息。 使用该注册宏需要包含以下头文件：”。《OpAICoreConfig构造函数》具体提供“OpAICoreConfig构造函数。”，它直接用于REGISTER_OP_AICORE_CONFIG 与 OpAICoreConfig、AddConfig、OpDef 的注册闭环。
- [OpAICoreDef](op_ai_core_def/op_ai_core_def.md)（`related`）：《OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）》的任务是“不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方式，针对不同的AI处理器型号注册差异化的算子原型。REGISTER_OP_AICORE_CONFIG宏在不改变原有注册的基础上，允许单独新增文件来注册算子在不同硬件形态上的差异化信息。 使用该注册宏需要包含以下头文件：”。《OpAICoreDef》具体提供“OpAICoreDef算子定义接口索引。”，它直接用于REGISTER_OP_AICORE_CONFIG 与 OpAICoreConfig、AddConfig、OpDef 的注册闭环。
- [原型注册接口（OP_ADD）](op_add.md)（`related`）：《OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）》的任务是“不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方式，针对不同的AI处理器型号注册差异化的算子原型。REGISTER_OP_AICORE_CONFIG宏在不改变原有注册的基础上，允许单独新增文件来注册算子在不同硬件形态上的差异化信息。 使用该注册宏需要包含以下头文件：”。《原型注册接口（OP_ADD）》具体提供“注册算子的原型定义，从而确保算子能够被框架正确识别、编译和执行。 算子原型主要描述了算子的输入输出、属性等信息以及算子在AI处理器上相关实现信息，并关联tiling实现等函数。算子原型通过自定义的算子类来承载，该算子类继承自OpDef类。完成算子的原型定义等操作后，需要调用OP_ADD接口，传入算子类型（自定义算子类的类名），进行算子原型注册。详细内容请参考算子原型定义。”，它直接用于REGISTER_OP_AICORE_CONFIG 与 OpAICoreConfig、AddConfig、OpDef 的注册闭环。
- [DynamicRankSupportFlag](op_ai_core_config/dynamic_rank_support_flag.md)（`same_topic`）：《DynamicRankSupportFlag》处理“标识算子是否支持dynamicRank（动态维度）。”。《OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）》提供“不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方式，针对不同的AI处理器型号注册差异化的算子原型。REGISTER_OP_AICORE_CONFIG宏在不改变原有注册的基础上，允许单独新增文件来注册算子在不同硬件形态上的差异化信息。 使用该注册宏需要包含以下头文件：”，其具体合同或探针直接接入DynamicRank 与 DynamicShape 配置及差异化原型注册入口。
<!-- cannbot:related:end -->
