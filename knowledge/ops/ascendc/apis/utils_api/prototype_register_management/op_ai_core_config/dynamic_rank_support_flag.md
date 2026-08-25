---
type: API
title: DynamicRankSupportFlag
description: 标识算子是否支持dynamicRank（动态维度）。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICoreConfig/DynamicRankSupportFlag.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# DynamicRankSupportFlag

## 功能说明
标识算子是否支持dynamicRank（动态维度）。
## 函数原型
## 参数说明
## 返回值说明
OpAICoreConfig类，请参考OpAICoreConfig。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [bisheng 动态 shape 编译段错误 — extern C + DTYPE](../../../../runbooks/compilation/bisheng_extern_c_dtype_dynamic_shape_segfault.md)（`exemplifies`）：bisheng 动态 shape 编译段错误 — extern C + DTYPE 与《DynamicRankSupportFlag》的实质衔接是：该动态 shape 崩溃与 extern C+DTYPE、动态声明和 TPL 选择形态直接相关，所选卡覆盖符号、flag 与模板入口对照。
- [DynamicShapeSupportFlag](dynamic_shape_support_flag.md)（`same_topic`）：《DynamicRankSupportFlag》处理“标识算子是否支持dynamicRank（动态维度）。”。《DynamicShapeSupportFlag》提供“用于标识该算子是否支持入图时的动态Shape场景。”，其具体合同或探针直接接入DynamicRank 与 DynamicShape 配置及差异化原型注册入口。
- [OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）](../register_op_aicore_config.md)（`same_topic`）：《DynamicRankSupportFlag》处理“标识算子是否支持dynamicRank（动态维度）。”。《OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）》提供“不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方式，针对不同的AI处理器型号注册差异化的算子原型。REGISTER_OP_AICORE_CONFIG宏在不改变原有注册的基础上，允许单独新增文件来注册算子在不同硬件形态上的差异化信息。 使用该注册宏需要包含以下头文件：”，其具体合同或探针直接接入DynamicRank 与 DynamicShape 配置及差异化原型注册入口。
<!-- cannbot:related:end -->
