---
type: API
title: GetSigmoidMaxMinTmpSize
description: 用于在host侧获取Sigmoid接口所需的最大最小临时空间大小，作为Tiling参数传递到kernel侧使用。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/Sigmoid_interface/GetSigmoidMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# GetSigmoidMaxMinTmpSize

kernel侧Sigmoid接口的计算需要开发者预留 申请临时空间，本接口用于在host侧获取预留 申请的最大最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。 - 为保证功能正确，预留 申请的临时空间大小不能小于最小临时空间大小； - 在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留 申请。

函数原型：void GetSigmoidMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：
- srcShape（输入）：输入的shape信息，参数类型为AscendC::TensorShape。
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- isReuseSource（输入）：是否复用源操作数输入的空间，与Sigmoid接口一致。
- maxValue（输出）：Sigmoid接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。
- minValue（输出）：Sigmoid接口能完成计算所需最小临时空间大小。为保证功能正确，接口计算时预留 申请的临时空间不能小于该数值。最小空间大小为0表示计算不需要临时空间。

<!-- cannbot:related:start -->
## 相关

- [Sigmoid](sigmoid.md)（`related`）：sharedTmpBuffer（输入）：临时缓存。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 用于Sigmoid内部复杂计算时存储中间变量，由开发者提供。 临时空间大小BufferSize的获取方式请参考GetSigmoidMaxMinTmpSize。；kernel侧Sigmoid接口的计算需要开发者预留 申请临时空间，本接口用于在host侧获取预留 申请的最大最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。；Host 侧容量查询直接为 Kernel 侧 Sigmoid 的 sharedTmpBuffer 选取合法大小，构成同一次调用的 Tiling 与执行链。
<!-- cannbot:related:end -->
