---
type: API
title: Isnan
description: 判断浮点数是否为nan。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/isnan.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Isnan

功能：判断浮点数是否为nan。

函数原型：bool isnan(float x)

参数：x（输入）源操作数。

返回值：false：输入非nan；true：输入为nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [IsNan](../../../simd_api/adv_api/math_compute/is_nan_interface/is_nan.md)（`related`）：SIMT Isnan 对单线程 float 标量判 NaN，高阶 IsNan 对 LocalTensor 批量判 NaN，可按执行模型选型。
- [IsNan接口](../../../simd_api/adv_api/math_compute/is_nan_interface/is_nan_interface.md)（`same_topic`）：《IsNan接口》处理“按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。”。《Isnan》提供“判断浮点数是否为nan。”，其具体合同或探针直接接入IsNan 的 Kernel/Tiling 合同、跨 dtype 谓词与 Cast 保留 NaN 的前置条件。
<!-- cannbot:related:end -->
