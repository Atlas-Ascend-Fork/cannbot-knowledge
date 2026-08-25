---
type: API
title: GetGeluMaxMinTmpSize
description: 在host侧获取Gelu系列接口所需最大最小临时空间大小，供开发者选择合适的Tiling参数传递到kernel侧。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/Gelu_interface/GetGeluMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetGeluMaxMinTmpSize

kernel侧Gelu、FasterGelu、FasterGeluV2接口的计算需要开发者预留 申请临时空间，本接口用于在host侧获取预留 申请的最大最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。 - 为保证功能正确，预留 申请的临时空间大小不能小于最小临时空间大小； - 在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留 申请。

函数原型：void GetGeluMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, uint32_t& maxValue, uint32_t& minValue)

参数：
- srcShape（输入）：输入的shape信息，参数类型为AscendC::TensorShape。
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- maxValue（输出）：Gelu、FasterGelu、FasterGeluV2接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。
- minValue（输出）：Gelu、FasterGelu、FasterGeluV2接口能完成计算所需最小临时空间大小。为保证功能正确，接口计算时预留 申请的临时空间不能小于该数值。最小空间大小为0表示计算不需要临时空间。

返回值：GetGeluMaxTmpSize返回kernel侧接口能完成计算所需最大临时空间大小。

<!-- cannbot:related:start -->
## 相关

- [FasterGelu](faster_gelu.md)（`related`）：FasterGelu 的 sharedTmpBuffer 由 Host 侧 GetGeluMaxMinTmpSize 按 shape 与 typeSize 给出合法上下界，最小值决定正确性、区间内增大空间可换取性能。
- [FasterGeluV2](faster_gelu_v2.md)（`related`）：V2 计算仍需按接口要求配置临时空间，不能沿用零 workspace 假设。
- [Gelu](gelu.md)（`same_topic`）：Gelu 与《GetGeluMaxMinTmpSize》的实质衔接是：Gelu 接口、快速近似变体和空间查询共同定义高精度/高性能调用；GeGLU 直接以 GELU 为门控，两个 runbook 给出 erfc 近似与负尾相消的可执行精度边界。
- [Gelu接口](gelu_interface.md)（`same_topic`）：GELU 总页定义计算与 workspace 查询流程。
<!-- cannbot:related:end -->
