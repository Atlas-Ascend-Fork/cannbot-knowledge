---
type: API
title: GetGeGLUMaxMinTmpSize
description: 在host侧获取GeGLU接口预留临时空间的最大和最小值，用于Tiling参数选择
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/GeGLU_interface/GetGeGLUMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetGeGLUMaxMinTmpSize

kernel侧GeGLU接口的计算需要开发者预留 申请临时空间，本接口用于在host侧获取预留 申请的最大最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。 - 为保证功能正确，预留 申请的临时空间大小不能小于最小临时空间大小； - 在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留 申请。

函数原型：void GetGeGLUMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：
- srcShape（输入）：输入的shape信息，参数类型为AscendC::TensorShape。
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- isReuseSource（输入）：是否复用源操作数输入的空间，与kernel侧接口一致。
- maxValue（输出）：GeGLU接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。
- minValue（输出）：GeGLU接口能完成计算所需最小临时空间大小。为保证功能正确，接口计算时预留 申请的临时空间不能小于该数值。最小空间大小为0表示计算不需要临时空间。

<!-- cannbot:related:start -->
## 相关

- [GetSwiGLUMaxMinTmpSize](../swi_glu_interface/get_swi_glu_max_min_tmp_size.md)（`related`）：SwiGLU 激活不同，临时空间公式不可直接复用；按门控函数选接口。
- [GeGLU](ge_glu.md)（`same_topic`）：GeGLU 与《GetGeGLUMaxMinTmpSize》的实质衔接是：GeGLU 直接调用 GELU 门控语义并要求独立临时缓冲；接口页和两种空间查询决定 tiling，GELU/Erf 卡解释其激活公式。
- [GeGLU接口](ge_glu_interface.md)（`same_topic`）：总页定义 GeGLU、workspace 查询和 factor-size 的完整调用流程。
- [GetGeGLUTmpBufferFactorSize](get_ge_glu_tmp_buffer_factor_size.md)（`same_topic`）：GetGeGLUTmpBufferFactorSize 与《GetGeGLUMaxMinTmpSize》的实质衔接是：该 factor 查询把 GeGLU 的 maxLiveNodeCount/extraBuf 与最大最小临时空间合并，直接推导 GeGLU 固定 UB 下的单次处理量。
<!-- cannbot:related:end -->
