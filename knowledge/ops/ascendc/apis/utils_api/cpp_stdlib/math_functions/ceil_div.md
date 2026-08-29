---
type: API
title: CeilDiv
description: 计算两个整数相除后向上取整的结果，可在Host侧和AI Core侧使用。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/math_functions/ceil_div.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ceil_div

头文件路径为："utils/std/cmath.h"。

计算两个整数a和b相除后向上取整的结果。该接口可在Host侧和AI Core侧使用。

函数原型：template <typename T, typename U>；__host__ __aicore__ inline constexpr auto ceil_div(const T& a, const U& b);

参数：T：参数a的数据类型，必须为整型。；U：参数b的数据类型，必须为整型。；a（输入）：被除数。；b（输入）：除数。

返回值：返回两个整型数相除的向上取整结果。一般情况下，返回值类型由decltype(T{} / U{})推导得到。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
约束：- T和U必须为整型，支持的数据类型：int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、int64_t、uint64_t。
- 当b为0时，结果为0。
- 对于有符号输入，调用方需确保a >= 0且b > 0。

<!-- cannbot:related:start -->
## 相关

- [Sigmoid 950 Direct Invoke 算子知识](../../../../operators/direct/nn/activation/sigmoid_950.md)（`related`）：“`totalLength==0` 会令 `blockDim==0`，之后 `CeilDiv(totalLength, blockDim)` 除零，因此空 tensor 不在该 Direct Invoke 的有效域内。”给出 Sigmoid 的具体失败调用；“计算两个整数a和b相除后向上取整的结果。该接口可在Host侧和AI Core侧使用。”给出 ceil_div 合同，直接支撑非零除数 guard 的实现与验证。
- [CeilDivision](../../../simd_api/basic_api/scalar_compute/ceil_division.md)（`same_topic`）：“计算两个整数a和b相除后向上取整的结果。该接口可在Host侧和AI Core侧使用。”与“计算两个整数num1和num2相除后向上取整结果。”提供双方正文证据。两端定义同一整数除法向上取整语义，分别服务 utils C++ 标准库接口和 SIMD 基础标量接口，适合按调用层选择。
<!-- cannbot:related:end -->
