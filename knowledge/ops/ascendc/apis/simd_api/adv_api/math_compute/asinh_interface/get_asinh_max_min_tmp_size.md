---
type: API
title: GetAsinhMaxMinTmpSize
description: 在host侧获取Asinh接口预留临时空间的最大和最小值，用于Tiling参数选择
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Asinh_interface/GetAsinhMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# GetAsinhMaxMinTmpSize

kernel侧Asinh接口的计算需要开发者预留 申请临时空间，本接口用于在host侧获取预留 申请的最大和最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。 - 为保证功能正确，预留 申请的临时空间大小不能小于最小临时空间大小； - 在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留 申请。

函数原型：void GetAsinhMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：
- srcShape（输入）：输入的shape信息，参数类型为AscendC::TensorShape。
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- isReuseSource（输入）：是否复用源操作数输入的空间，与Asinh接口一致。
- maxValue（输出）：Asinh接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。
- minValue（输出）：Asinh接口能完成计算所需最小临时空间大小。为保证功能正确，接口计算时预留 申请的临时空间不能小于该数值。最小空间大小为0表示计算不需要临时空间。

<!-- cannbot:related:start -->
## 相关

- [Asinhf](../../../../simt_api/math_functions/float_math_functions/asinhf.md)（`related`）：高阶路径需先配置 workspace。
- [GetSinhMaxMinTmpSize](../sinh_interface/get_sinh_max_min_tmp_size.md)（`related`）：Asinh 是反函数且临时空间公式不同；不能因名称接近复用 Sinh 的 workspace 估算。
- [Asinh](asinh.md)（`same_topic`）：《GetAsinhMaxMinTmpSize》的任务是“在host侧获取Asinh接口预留临时空间的最大和最小值，用于Tiling参数选择”。《Asinh》具体提供“按元素做反双曲正弦函数计算，输入值域需在-65504到65504范围内”，它直接用于Asinh workspace 上下界和 factor 到 Kernel 的同一空间合同。
- [Asinh接口](asinh_interface.md)（`same_topic`）：《GetAsinhMaxMinTmpSize》的任务是“在host侧获取Asinh接口预留临时空间的最大和最小值，用于Tiling参数选择”。《Asinh接口》具体提供“提供Asinh反双曲正弦计算接口及其Tiling临时空间大小查询接口，包含Asinh、GetAsinhMaxMinTmpSize等。”，它直接用于Asinh workspace 上下界和 factor 到 Kernel 的同一空间合同。
- [GetAsinhTmpBufferFactorSize](get_asinh_tmp_buffer_factor_size.md)（`same_topic`）：《GetAsinhMaxMinTmpSize》的任务是“在host侧获取Asinh接口预留临时空间的最大和最小值，用于Tiling参数选择”。《GetAsinhTmpBufferFactorSize》具体提供“获取Asinh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数”，它直接用于Asinh workspace 上下界和 factor 到 Kernel 的同一空间合同。
<!-- cannbot:related:end -->
