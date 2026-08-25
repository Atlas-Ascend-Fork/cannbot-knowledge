---
type: API
title: sqrt（数学函数）
description: 计算输入数据的平方根。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/math_functions/sqrt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# sqrt

计算输入数据的平方根。

函数原型：template <typename T>；__aicore__ inline T sqrt(const T src)

参数：T：输入数据src的数据类型。当前支持的数据类型为float、int64_t。；src（输入）：源操作数。

返回值：输入数据的平方根。

对于数据类型为int64_t的数据，其计算结果将被截断为整数。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
约束：输入必须为非负数。若输入为负数，则接口返回值无意义。

<!-- cannbot:related:start -->
## 相关

- [bisheng 不接受 device 侧 sqrtf—改用向量 Sqrt](../../../../runbooks/compilation/device_sqrt_uses_vector_api.md)（`exemplifies`）：bisheng 不接受 device 侧 sqrtf—改用向量 Sqrt说明device kernel 中直接调用 sqrtf 导致 bisheng 编译失败；改为 32B 对齐的向量 Sqrt 链并显式同步。
- [AscSqrt](../../../simd_api/c_api/reg/arithmetic_compute/asc_sqrt.md)（`related`）：AscSqrt说明根据mask对源操作数src按元素求开方，将结果写入目的操作数dst。
- [AscSqrt](../../../simd_api/c_api/vector_compute/asc_sqrt.md)（`related`）：AscSqrt说明asc_sqrt（矢量计算）。
- [Sqrt](../../../simd_api/basic_api/memory_vector_compute/basic_arithmetic/sqrt.md)（`related`）：Sqrt说明单目矢量计算接口，对输入tensor按元素做开方。
- [Sqrt](../../../simd_api/basic_api/reg_vector_compute/basic_arithmetic/sqrt.md)（`related`）：Sqrt说明根据mask对源操作数srcReg逐元素做平方根运算，将结果写入目的操作数dstReg。
<!-- cannbot:related:end -->
