---
type: API
title: GetAsinMaxMinTmpSize
description: 在host侧获取Asin接口预留临时空间的最大和最小值，用于Tiling参数选择
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Asin_interface/GetAsinMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# GetAsinMaxMinTmpSize

kernel侧Asin接口的计算需要开发者预留 申请临时空间，本接口用于在host侧获取预留 申请的最大和最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。 - 为保证功能正确，预留 申请的临时空间大小不能小于最小临时空间大小； - 在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留 申请。

函数原型：void GetAsinMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：
- srcShape（输入）：输入的shape信息，参数类型为AscendC::TensorShape。
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- isReuseSource（输入）：是否复用源操作数输入的空间，与Asin接口一致。
- maxValue（输出）：Asin接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。
- minValue（输出）：Asin接口能完成计算所需最小临时空间大小。为保证功能正确，接口计算时预留 申请的临时空间不能小于该数值。最小空间大小为0表示计算不需要临时空间。

<!-- cannbot:related:start -->
## 相关

- [Asin](asin.md)（`related`）：临时空间大小BufferSize的获取方式请参考GetAsinMaxMinTmpSize。；本接口用于在host侧获取预留 申请的最大和最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。。Asin 明确把临时空间取得步骤交给右侧 Host 接口，右侧产生的范围又直接成为 Asin Kernel 的 Tiling 输入；两者是计算接口与资源查询 helper 的互补任务链，并非同一操作。
- [GetAsinTmpBufferFactorSize](get_asin_tmp_buffer_factor_size.md)（`related`）：通过maxLiveNodeCount和extraBuf可以推算算子单次最大计算元素数量；开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。最大/最小接口先确定合法临时空间范围，factor 接口再把已选空间换算成单次元素容量；两端组成 Host Tiling 选 buffer、Kernel 按容量分块的闭环。
<!-- cannbot:related:end -->
