---
type: API
title: Acoshf
description: 获取输入数据的双曲反余弦值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/acoshf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Acoshf

功能：获取输入数据的双曲反余弦值。

函数原型：float acoshf(float x)

参数：x（输入）源操作数。

返回值：输入数据的双曲反余弦值。特殊值：inf→inf；-inf→nan；nan→nan。

约束：本接口支持的输入数据为[1, 65504.0]范围内的数据。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Acosh](../../../simd_api/adv_api/math_compute/acosh_interface/acosh.md)（`same_topic`）：《Acoshf》明确“获取输入数据的双曲反余弦值。”；它与《Acosh》的“按元素做双曲反余弦函数计算，输入值域需在1到65504范围内”在实际调用参数、数据流或结果校验上直接衔接。
- [Acosh接口](../../../simd_api/adv_api/math_compute/acosh_interface/acosh_interface.md)（`same_topic`）：Acoshf 与《Acosh接口》的实质衔接是：Acoshf 是标量双曲反余弦；Acosh 高阶接口及空间查询是 tensor 版本，Coshf 是其反函数，可用于定义域和往返验证。
- [Coshf](coshf.md)（`same_topic`）：Acoshf 与《Coshf》的实质衔接是：Acoshf 是标量双曲反余弦；Acosh 高阶接口及空间查询是 tensor 版本，Coshf 是其反函数，可用于定义域和往返验证。
- [GetAcoshMaxMinTmpSize](../../../simd_api/adv_api/math_compute/acosh_interface/get_acosh_max_min_tmp_size.md)（`same_topic`）：Acoshf 与《GetAcoshMaxMinTmpSize》的实质衔接是：Acoshf 是标量双曲反余弦；Acosh 高阶接口及空间查询是 tensor 版本，Coshf 是其反函数，可用于定义域和往返验证。
- [GetAcoshTmpBufferFactorSize](../../../simd_api/adv_api/math_compute/acosh_interface/get_acosh_tmp_buffer_factor_size.md)（`same_topic`）：Acoshf 与《GetAcoshTmpBufferFactorSize》的实质衔接是：Acoshf 是标量双曲反余弦；Acosh 高阶接口及空间查询是 tensor 版本，Coshf 是其反函数，可用于定义域和往返验证。
<!-- cannbot:related:end -->
