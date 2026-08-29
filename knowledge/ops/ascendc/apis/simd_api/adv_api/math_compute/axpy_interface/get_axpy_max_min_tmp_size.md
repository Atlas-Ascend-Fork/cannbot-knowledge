---
type: API
title: GetAxpyMaxMinTmpSize
description: 在host侧获取Axpy接口申请临时空间的最大和最小值，用于Tiling参数选择
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Axpy_interface/GetAxpyMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# GetAxpyMaxMinTmpSize

kernel侧Axpy接口的计算需要开发者申请临时空间，本接口用于在host侧获取申请的最大和最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。 - 为保证功能正确，申请的临时空间大小不能小于最小临时空间大小； - 在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间申请。

函数原型：void GetAxpyMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：
- srcShape（输入）：输入的shape信息，参数类型为AscendC::TensorShape。
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- isReuseSource（输入）：是否复用源操作数输入的空间，与Axpy接口一致。
- maxValue（输出）：Axpy接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间申请。
- minValue（输出）：Axpy接口能完成计算所需最小临时空间大小。为保证功能正确，接口计算时申请的临时空间不能小于该数值。最小空间大小为0表示计算不需要临时空间。

<!-- cannbot:related:start -->
## 相关

- [Axpy](axpy.md)（`related`）：源操作数(srcTensor)中每个元素与标量求积后和目的操作数(dstTensor)中的对应元素相加，计算公式如下： 该接口功能同基础API Axpy，区别在于此接口指令是通过Muls和Add组合计算，从而提供更优的精度。；kernel侧Axpy接口的计算需要开发者申请临时空间，本接口用于在host侧获取申请的最大和最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。；Axpy 定义 kernel 运算，Host helper 给出该运算的合法临时空间区间和 Tiling 传递方式，构成资源规划任务链。
- [Axpy接口](axpy_interface.md)（`same_topic`）：kernel侧Axpy接口的计算需要开发者申请临时空间，本接口用于在host侧获取申请的最大和最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。；临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。前者产生 Axpy 的空间上下界，后者规定该值如何供 Kernel 的 sharedTmpBuffer 使用。
<!-- cannbot:related:end -->
