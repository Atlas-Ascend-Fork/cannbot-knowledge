---
type: API
title: __uint2half_rn
description: 遵循CAST_RINT模式，将uint32类型数据转换为half类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__uint2half_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __uint2half_rn

功能：遵循CAST_RINT模式，将uint32类型数据转换为half类型数据，返回转换后的值。

函数原型：half __uint2half_rn(const unsigned int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_RINT模式转换成的half类型数据。特殊值：0→0；2049→2048；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；65505→ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__uint2half_rn_sat](_uint2half_rn_sat.md)（`same_topic`）：约束：SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。需包含头文件 simt_api/asc_fp16.h。；功能：遵循CAST_RINT模式，将uint32类型数据转换为half类型数据，返回转换后的值。。带 sat 名称的接口在 SIMT 场景明确说明饱和模式不生效，而非 sat 接口执行同样的 uint32→half CAST_RINT 转换，因此当前平台下二者的有效转换核心一致。
<!-- cannbot:related:end -->
