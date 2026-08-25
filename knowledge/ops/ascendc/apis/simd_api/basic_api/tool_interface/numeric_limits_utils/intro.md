---
type: API
title: 工具接口简介
description: NumericLimits工具类，用于查询指定数据类型的最大值/最小值等属性。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/NumericLimits_utils/intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 工具接口简介

NumericLimits工具类，用于查询指定数据类型的最大值/最小值等属性。

返回指定数据类型的最大有限值。

本接口组包含 Max, Lowest, Min, Infinity, NegativeInfinity。

返回值：标量接口返回值为对应数据类型的最大有限值。 矢量接口无返回值。 表 2 Max各数据类型输出

约束：标量接口无约束，矢量接口使用duplicate填充前count个元素赋最大有限值，参照Memory矢量计算下的数据填充接口duplicate约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
