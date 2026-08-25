---
type: API
title: GetTruncMaxMinTmpSize
description: 在host侧获取Trunc接口计算所需最大和最小临时空间大小，供Tiling参数选择。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Trunc_interface/GetTruncMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetTruncMaxMinTmpSize

host侧Tiling接口，用于获取Trunc接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetTruncMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Trunc接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [AscTrunc](../../../c_api/reg/data_type_convert/asc_trunc.md)（`related`）：《AscTrunc》说明将浮点数按TRUNC（向零方向截断）截断为整数值，结果保持原浮点类型。；《GetTruncMaxMinTmpSize》说明在host侧获取Trunc接口计算所需最大和最小临时空间大小，供Tiling参数选择。。二者在AscTrunc与Memory Trunc、SIMT half/bfloat16/float变体共享向零截断语义，workspace查询用于高阶接口分块上存在可执行的直接衔接。
- [Trunc](trunc.md)（`related`）：GetTruncMaxMinTmpSize 按 shape/typeSize/isReuseSource 给出 Kernel Trunc 临时空间的硬下界与性能上界。
- [GetTruncTmpBufferFactorSize](get_trunc_tmp_buffer_factor_size.md)（`same_topic`）：GetTruncMaxMinTmpSize 的核心契约是“在host侧获取Trunc接口计算所需最大和最小临时空间大小，供Tiling参数选择”；GetTruncTmpBufferFactorSize 补充“获取maxLiveNodeCount和extraBuf，用于推算Trunc接口在固定临时空间下单次最大计算元素数量”。
- [Truncf](../../../../simt_api/math_functions/float_math_functions/truncf.md)（`same_topic`）：Truncf 与《GetTruncMaxMinTmpSize》的实质衔接是：Truncf 与 SIMD、基础、C、half/half2/bfloat16x2 Trunc 都实现向零截断；空间查询只适用于高阶 tensor 版本，不能套到标量入口。
- [Trunc接口](trunc_interface.md)（`same_topic`）：GetTruncMaxMinTmpSize 的核心契约是“在host侧获取Trunc接口计算所需最大和最小临时空间大小，供Tiling参数选择”；Trunc接口 补充“按元素做浮点数截断（向零取整），并提供临时空间大小获取接口”。
<!-- cannbot:related:end -->
