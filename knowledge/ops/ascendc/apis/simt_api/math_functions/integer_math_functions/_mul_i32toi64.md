---
type: API
title: __mul_i32toi64
description: 计算输入32位整数x和y的乘积，返回64位结果。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__mul_i32toi64.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __mul_i32toi64

32 位扩展为 64 位的乘法函数。计算输入 32 位整数 x 和 y 的乘积，返回 64 位结果。

函数原型（重载）：long long __mul_i32toi64(int x, int y)、unsigned long long __mul_i32toi64(unsigned int x, unsigned int y)

参数 x、y 为源操作数（乘数）。返回乘积的 64 位结果。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [SimThreadExponential 950 ACLNN 算子知识](../../../../operators/aclnn/math/random/sim_thread_exponential_950.md)（`related`）：焦点卡定义“计算输入 32 位整数 x 和 y 的乘积，返回 64 位结果。”，候选算子在 Philox 热路径实际执行“uint64_t res0_u64 = __mul_i32toi64(PHILOX_M4X32_A, counter［0］);”；API 的 64 位乘积合同直接支撑随机数 round 的高低 32 位复用。
<!-- cannbot:related:end -->
