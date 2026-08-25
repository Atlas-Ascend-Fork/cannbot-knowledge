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
