---
type: API
title: __uint2half_rz
description: 遵循CAST_TRUNC模式，将uint32类型数据转换为half类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__uint2half_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __uint2half_rz

功能：遵循CAST_TRUNC模式，将uint32类型数据转换为half类型数据，返回转换后的值。

函数原型：half __uint2half_rz(const unsigned int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_TRUNC模式转换成的half类型数据。特殊值：2049→2048；4097→4096；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；65505→ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__uint2half_rz_sat](_uint2half_rz_sat.md)（`related`）：“特殊值：2049→2048；4097→4096；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16”给出焦点端事实；“本接口的饱和模式不生效。”给出候选端事实。普通 RZ 卡给出截断与最大值行为，RZ_SAT 卡明确 SAT 在 SIMT 场景不生效；联合阅读可避免把后缀误当作额外饱和保证。
<!-- cannbot:related:end -->
