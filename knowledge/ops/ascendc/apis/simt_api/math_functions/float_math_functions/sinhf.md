---
type: API
title: Sinhf
description: 获取输入数据的双曲正弦值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/sinhf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Sinhf

功能：获取输入数据的双曲正弦值。

函数原型：float sinhf(float x)

参数：x（输入）源操作数。

返回值：输入数据的双曲正弦值。特殊值：inf→inf；-inf→-inf；nan→nan；0→0。

约束：本接口支持的输入数据为[-89.4, 89.4]范围内的数据。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Asinhf](asinhf.md)（`related`）：Sinh 是反函数，可在有限域做往返验证。
- [GetSinhMaxMinTmpSize](../../../simd_api/adv_api/math_compute/sinh_interface/get_sinh_max_min_tmp_size.md)（`related`）：选择高阶 Tensor Sinh 时需先据元素数获取 workspace 上下界，补充 SIMT 标量调用没有的缓冲契约。
- [Sinh接口](../../../simd_api/adv_api/math_compute/sinh_interface/sinh_interface.md)（`same_topic`）：高阶 Sinh 总页定义 LocalTensor 版本及临时空间获取流程，与 SIMT sinhf 完成相同双曲正弦任务。
<!-- cannbot:related:end -->
