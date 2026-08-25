---
type: API
title: __hisnan
description: 判断浮点数是否为nan。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_compare_functions/__hisnan.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hisnan

功能：判断浮点数是否为nan。

函数原型：bool __hisnan(half x)

参数：x（输入）源操作数。

返回值：返回是否为nan的结果。输入为非nan返回false，输入为nan返回true。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [IsNan接口](../../../../simd_api/adv_api/math_compute/is_nan_interface/is_nan_interface.md)（`related`）：《IsNan接口》处理“按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。”。《__hisnan》提供“判断浮点数是否为nan。”，其具体合同或探针直接接入IsNan 的 Kernel/Tiling 合同、跨 dtype 谓词与 Cast 保留 NaN 的前置条件。
- [__heq](_heq.md)（`related`）：IsNaN 可显式验证 Eq/Equ 的 NaN 分支。
- [__isnanx2](../half2_compare_functions/_isnanx2.md)（`related`）：标量 half NaN 判定可作为 __isnanx2 每个分量的验证 oracle。
<!-- cannbot:related:end -->
