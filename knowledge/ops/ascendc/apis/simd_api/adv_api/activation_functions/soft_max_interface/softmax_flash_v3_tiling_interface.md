---
type: API
title: SoftmaxFlashV3 Tiling接口
description: 用于获取SoftmaxFlashV3接口所需的Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SoftMax_interface/SoftmaxFlashV3_Tiling_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SoftmaxFlashV3 Tiling接口

用于获取SoftmaxFlashV3接口所需的Tiling参数。

函数原型：
void GetSoftMaxFlashV3MaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t dataTypeSize1, const uint32_t dataTypeSize2, uint32_t& maxValue, uint32_t& minValue, const bool isUpdate, const bool isBasicBlock = false)
void SoftMaxFlashV3TilingFunc(const AscendC::TensorShape& srcShape, const uint32_t dataTypeSize1, const uint32_t dataTypeSize2,const uint32_t localWorkSpaceSize, optiling::SoftMaxTiling& softmaxFlashV3Tiling, const bool isUpdate,const bool isBasicBlock = false)

参数：
- srcShape（输入）：输入srcTensor的shape信息，参数类型为AscendC::TensorShape。
- dataTypeSize1（输入）：输入srcTensor的数据类型大小，即对应SoftMaxFlashV3 Kernel函数中模板参数T的数据类型大小。当前模板参数T仅支持half类型，故此参数只支持取值为2。
- dataTypeSize2（输入）：inMeanTensor、inExpSumTensor 和 inMaxTensor 的元素字节数，对应 kernel 模板参数 U；U 当前仅支持 float，因此该参数只能取 4。
- maxValue（输出）：SoftMaxFlashV3接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。
- minValue（输出）：SoftMaxFlashV3接口能完成计算所需最小临时空间大小。为保证功能正确，接口计算时预留 申请的临时空间不能小于该数值。最小空间大小为0表示计算不需要临时空间。

<!-- cannbot:related:start -->
## 相关

- [flash在线softmax JIT重排致精度超阈](../../../../../runbooks/precision/flash_softmax_jit.md)（`exemplifies`）：《SoftmaxFlashV3 Tiling接口》处理“用于获取SoftmaxFlashV3接口所需的Tiling参数。”。《flash在线softmax JIT重排致精度超阈》明确“flash 在线 softmax 的 mi/li/oi 循环依赖对执行顺序敏感；loop_unroll_list、device_sched_mode、cube_nbuffer_setting 任一调离默认值都会改变 C1 任务执行顺序，引入 BF16 ULP 级累积误差 0.00048828 超逐位置阈值，三参数对在线 softmax 算子 banned。”，可直接用于核对SoftmaxFlashV3 的 Kernel 参数、专用 Tiling、update 状态与在线 softmax 数值依赖。
- [unroll s2 内层循环破坏 flash 在线 softmax 循环态](../../../../../runbooks/precision/unroll_s2_flash_softmax.md)（`exemplifies`）：《SoftmaxFlashV3 Tiling接口》处理“用于获取SoftmaxFlashV3接口所需的Tiling参数。”。《unroll s2 内层循环破坏 flash 在线 softmax 循环态》明确“对 flash attention 主循环 FLASH_LOOP_L4_s2_SA 把 unroll_list 由 {1} 扩为 {1,2} 会破坏 is_loop_begin/end 的循环态边界，使在线 softmax 的 li/mi 状态在 s2 步间错位、atten_out 大面积精度回归（8306526 误差点/阈值 41943，max_diff 0.066）。该展开路线 banned，性能优化改走 pass_option/TileShape。”，可直接用于核对SoftmaxFlashV3 的 Kernel 参数、专用 Tiling、update 状态与在线 softmax 数值依赖。
- [SoftmaxFlash](softmax_flash.md)（`related`）：《SoftmaxFlashV3 Tiling接口》处理“用于获取SoftmaxFlashV3接口所需的Tiling参数。”。《SoftmaxFlash》明确“Softmax增强版本，可根据上一次Softmax计算的sum和max更新本次结果，适用于last轴切轴场景，不开启update时等同于SoftMax。即将废弃，建议使用SoftmaxFlashV2。”，可直接用于核对SoftmaxFlashV3 的 Kernel 参数、专用 Tiling、update 状态与在线 softmax 数值依赖。
- [SoftmaxFlash Tiling接口](softmax_flash_tiling_interface.md)（`related`）：《SoftmaxFlashV3 Tiling接口》处理“用于获取SoftmaxFlashV3接口所需的Tiling参数。”。《SoftmaxFlash Tiling接口》明确“注意：该接口后续即将废弃，新开发内容不要使用该接口。 用于获取SoftmaxFlash Tiling参数。”，可直接用于核对SoftmaxFlashV3 的 Kernel 参数、专用 Tiling、update 状态与在线 softmax 数值依赖。
- [SoftmaxFlashV2](softmax_flash_v2.md)（`related`）：《SoftmaxFlashV3 Tiling接口》处理“用于获取SoftmaxFlashV3接口所需的Tiling参数。”。《SoftmaxFlashV2》明确“SoftmaxFlash增强版本，对应FlashAttention-2算法，支持通过isUpdate参数控制是否根据前一次的sum和max更新当前结果，支持ND和NZ格式。”，可直接用于核对SoftmaxFlashV3 的 Kernel 参数、专用 Tiling、update 状态与在线 softmax 数值依赖。
- [SoftmaxFlashV2 Tiling接口](softmax_flash_v2_tiling_interface.md)（`related`）：《SoftmaxFlashV3 Tiling接口》处理“用于获取SoftmaxFlashV3接口所需的Tiling参数。”。《SoftmaxFlashV2 Tiling接口》明确“用于获取SoftmaxFlashV2接口所需的Tiling参数。”，可直接用于核对SoftmaxFlashV3 的 Kernel 参数、专用 Tiling、update 状态与在线 softmax 数值依赖。
- [SoftmaxFlashV3](softmax_flash_v3.md)（`same_topic`）：《SoftmaxFlashV3 Tiling接口》处理“用于获取SoftmaxFlashV3接口所需的Tiling参数。”。《SoftmaxFlashV3》明确“SoftmaxFlash增强版本，对应Softmax PASA算法。对输入tensor尾轴切分并按update模式计算softmax的均值、最大值和指数和，仅支持ND格式输入。”，可直接用于核对SoftmaxFlashV3 的 Kernel 参数、专用 Tiling、update 状态与在线 softmax 数值依赖。
<!-- cannbot:related:end -->
