---
type: API
title: GetSwiGLUMaxMinTmpSize
description: 在host侧获取SwiGLU接口预留临时空间的最大和最小值，用于Tiling参数选择
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SwiGLU_interface/GetSwiGLUMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# GetSwiGLUMaxMinTmpSize

kernel侧SwiGLU接口的计算需要开发者预留 申请临时空间，本接口用于在host侧获取预留 申请的最大最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。 - 为保证功能正确，预留 申请的临时空间大小不能小于最小临时空间大小； - 在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留 申请。

函数原型：void GetSwiGLUMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, uint32_t& maxValue, uint32_t& minValue, const bool isReuseSource)

参数：
- srcShape（输入）：输入的shape信息，参数类型为AscendC::TensorShape。
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- maxValue（输出）：SwiGLU接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。
- minValue（输出）：SwiGLU接口能完成计算所需最小临时空间大小。为保证功能正确，接口计算时预留 申请的临时空间不能小于该数值。最小空间大小为0表示计算不需要临时空间。
- isReuseSource（输入）：是否复用源操作数输入的空间，与kernel侧接口一致。

<!-- cannbot:related:start -->
## 相关

- [SwiGLU 高级 API 在非32B对齐 slice 上精度失败](../../../../../runbooks/precision/swiglu_adv_api_fails_non_32b_aligned_slice.md)（`exemplifies`）：该排障卡记录 SwiGLU 在非 32B 对齐 slice 上即使按接口准备空间仍出现边界精度失败，补充了查询契约之外的实测失效边界。
- [GetGeGLUMaxMinTmpSize](../ge_glu_interface/get_ge_glu_max_min_tmp_size.md)（`related`）：SwiGLU 激活不同，临时空间公式不可直接复用；按门控函数选接口。
- [GetSwiGLUTmpBufferFactorSize](get_swi_glu_tmp_buffer_factor_size.md)（`same_topic`）：两者是 SwiGLU Host 侧临时空间预算的互补查询：本接口给出合法上下界，FactorSize 接口用 live-node/factor 模型估算可处理规模。
- [SwiGLU](swi_glu.md)（`same_topic`）：SwiGLU 与《GetSwiGLUMaxMinTmpSize》的实质衔接是：SwiGLU 的 kernel、两种临时空间查询与非 32B slice 精度故障共同约束调用和缓冲区分配。
<!-- cannbot:related:end -->
