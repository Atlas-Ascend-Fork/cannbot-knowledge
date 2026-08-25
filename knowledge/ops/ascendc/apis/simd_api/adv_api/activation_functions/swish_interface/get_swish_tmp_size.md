---
type: API
title: GetSwishTmpSize
description: 用于获取Swish Tiling参数：Swish接口能完成计算所需最大临时空间大小和最小临时空间大小。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/Swish_interface/GetSwishTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetSwishTmpSize

用于获取Swish Tiling参数：Swish接口能完成计算所需最大临时空间大小和最小临时空间大小。

函数原型：inline void GetSwishTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：
- srcShape（输入）：输入的shape信息，参数类型为AscendC::TensorShape。
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2，即sizeof(half)。
- isReuseSource（输入）：是否复用源操作数输入的空间，与kernel侧接口一致。
- maxValue（输出）：Swish接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。
- minValue（输出）：Swish接口能完成计算所需最小临时空间大小。为保证功能正确，接口计算时预留 申请的临时空间不能小于该数值。最小空间大小为0表示计算不需要临时空间。

<!-- cannbot:related:start -->
## 相关

- [Swish接口](swish_interface.md)（`related`）：GetSwishTmpSize 为 Swish Kernel 的中间变量预留提供直接空间预算。
- [Swish](swish.md)（`same_topic`）：Swish 与《GetSwishTmpSize》的实质衔接是：Swish kernel 与临时空间查询直接配套；SiLU 是 beta=1 的同公式变体，Sigmoid 是门控项。
<!-- cannbot:related:end -->
