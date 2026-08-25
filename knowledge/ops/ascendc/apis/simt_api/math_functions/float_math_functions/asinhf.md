---
type: API
title: Asinhf
description: 获取输入数据的双曲反正弦值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/asinhf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Asinhf

功能：获取输入数据的双曲反正弦值。

函数原型：float asinhf(float x)

参数：x（输入）源操作数。

返回值：输入数据的双曲反正弦值。特殊值：inf→inf；-inf→-inf；nan→nan；0→0。

约束：本接口支持的输入数据为[-65504.0, 65504.0]范围内的数据。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Asinh接口](../../../simd_api/adv_api/math_compute/asinh_interface/asinh_interface.md)（`related`）：《Asinhf》明确“获取输入数据的双曲反正弦值。”；它与《Asinh接口》的“提供Asinh反双曲正弦计算接口及其Tiling临时空间大小查询接口，包含Asinh、GetAsinhMaxMinTmpSize等。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetAsinhMaxMinTmpSize](../../../simd_api/adv_api/math_compute/asinh_interface/get_asinh_max_min_tmp_size.md)（`related`）：高阶路径需先配置 workspace。
- [Sinhf](sinhf.md)（`related`）：Sinh 是反函数，可在有限域做往返验证。
- [Asinh](../../../simd_api/adv_api/math_compute/asinh_interface/asinh.md)（`same_topic`）：高阶 Tensor Asinh 与 SIMT asinhf 完成同一反双曲正弦。
<!-- cannbot:related:end -->
