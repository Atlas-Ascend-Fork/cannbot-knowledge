---
type: API
title: GetSinhMaxMinTmpSize
description: 在host侧获取Sinh接口计算所需最大和最小临时空间大小，供Tiling参数选择。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Sinh_interface/GetSinhMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetSinhMaxMinTmpSize

host侧Tiling接口，用于获取Sinh接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetSinhMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Sinh接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [GetAsinhMaxMinTmpSize](../asinh_interface/get_asinh_max_min_tmp_size.md)（`related`）：Asinh 是反函数且临时空间公式不同；不能因名称接近复用 Sinh 的 workspace 估算。
- [Sinh](sinh.md)（`related`）：Sinh 的显式临时空间重载依赖对应 MaxMin 接口预算，且 calCount 只改变参与元素数，不取消 buffer 约束。
- [Sinhf](../../../../simt_api/math_functions/float_math_functions/sinhf.md)（`related`）：选择高阶 Tensor Sinh 时需先据元素数获取 workspace 上下界，补充 SIMT 标量调用没有的缓冲契约。
- [GetSinhTmpBufferFactorSize](get_sinh_tmp_buffer_factor_size.md)（`same_topic`）：GetSinhTmpBufferFactorSize 与《GetSinhMaxMinTmpSize》的实质衔接是：该因子查询服务 Sinh 高阶接口，必须结合最大最小空间查询把 host 侧预算转换成 kernel 单次处理量。
- [Sinh接口](sinh_interface.md)（`same_topic`）：Sinh 总页定义该 MaxMinTmpSize 查询与 Kernel 调用的组合方式。
<!-- cannbot:related:end -->
