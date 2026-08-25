---
type: API
title: GetCeilMaxMinTmpSize
description: 在host侧获取Ceil接口预留临时空间的最大和最小值，用于Tiling参数选择
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Ceil_interface/GetCeilMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# GetCeilMaxMinTmpSize

kernel侧Ceil接口的计算需要开发者预留 申请临时空间，本接口用于在host侧获取预留 申请的最大和最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。 - 为保证功能正确，预留 申请的临时空间大小不能小于最小临时空间大小； - 在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留 申请。

函数原型：void GetCeilMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：
- srcShape（输入）：输入的shape信息，参数类型为AscendC::TensorShape。
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- isReuseSource（输入）：是否复用源操作数输入的空间，与Ceil接口一致。
- maxValue（输出）：Ceil接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。
- minValue（输出）：Ceil接口能完成计算所需最小临时空间大小。为保证功能正确，接口计算时预留 申请的临时空间不能小于该数值。最小空间大小为0表示计算不需要临时空间。

<!-- cannbot:related:start -->
## 相关

- [Ceil](ceil.md)（`same_topic`）：Ceil 与《GetCeilMaxMinTmpSize》的实质衔接是：Ceil kernel 依赖两种临时空间查询，C API 是对应入口，Floor 提供相反取整边界；多核尾块卡直接验证 remaining 计数错误。
- [Ceil接口](ceil_interface.md)（`same_topic`）：《Ceil接口》说明提供Ceil向上取整计算接口及其Tiling临时空间大小查询接口，包含Ceil、GetCeilMaxMinTmpSize等。；《GetCeilMaxMinTmpSize》说明在host侧获取Ceil接口预留临时空间的最大和最小值，用于Tiling参数选择。二者在Ceil计算、临时空间估算与多核尾段切分共同决定向上取整算子的正确执行上存在可执行的直接衔接。
- [GetCeilTmpBufferFactorSize](get_ceil_tmp_buffer_factor_size.md)（`same_topic`）：MaxMin 接口给出 Ceil workspace 合法区间，factor 接口再由实际空间反算单次处理量，是同一 tiling 公式的正反两侧。
<!-- cannbot:related:end -->
