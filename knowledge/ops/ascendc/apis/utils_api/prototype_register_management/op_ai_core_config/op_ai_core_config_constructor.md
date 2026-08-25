---
type: API
title: OpAICoreConfig构造函数
description: OpAICoreConfig构造函数。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICoreConfig/OpAICoreConfig_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# OpAICoreConfig构造函数

## 功能说明
OpAICoreConfig构造函数。
## 函数原型
## 参数说明
soc：输入：AI处理器型号。
aicore_config：输入：已构造完成的OpAICoreConfig，用于拷贝构造OpAICoreConfig。
## 返回值说明
无
## 约束说明
传入soc入参的构造函数会对OpAICoreConfig结构中的部分参数进行初始化，具体的参数和初始化值如下表所示：
无入参的默认构造函数不会初始化上述参数。
拷贝构造函数会复制被拷贝对象中已配置的输入、输出和配置项信息。

<!-- cannbot:related:start -->
## 相关

- [def.cpp 缺 AddConfig 致 SOC_NOT_SUPPORT](../../../../runbooks/compilation/def_cpp_addconfig_soc_not_support.md)（`exemplifies`）：OpAICoreConfig构造函数 与《def.cpp 缺 AddConfig 致 SOC_NOT_SUPPORT》的实质衔接是：OpAICoreConfig 构造后配置动态能力、输入输出、tiling/support，并注册到 OpAICoreDef。
- [OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）](../register_op_aicore_config.md)（`related`）：《OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）》的任务是“不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方式，针对不同的AI处理器型号注册差异化的算子原型。REGISTER_OP_AICORE_CONFIG宏在不改变原有注册的基础上，允许单独新增文件来注册算子在不同硬件形态上的差异化信息。 使用该注册宏需要包含以下头文件：”。《OpAICoreConfig构造函数》具体提供“OpAICoreConfig构造函数。”，它直接用于REGISTER_OP_AICORE_CONFIG 与 OpAICoreConfig、AddConfig、OpDef 的注册闭环。
- [operator =](operator.md)（`related`）：赋值运算符把已有 OpAICoreConfig 的输入、输出和动态能力配置复制到已构造对象；构造函数定义目标对象初始状态。
- [AddConfig（OpAICoreDef）](../op_ai_core_def/add_config.md)（`same_topic`）：OpAICoreConfig构造函数 与《AddConfig（OpAICoreDef）》的实质衔接是：OpAICoreConfig 构造后配置动态能力、输入输出、tiling/support，并注册到 OpAICoreDef。
<!-- cannbot:related:end -->
