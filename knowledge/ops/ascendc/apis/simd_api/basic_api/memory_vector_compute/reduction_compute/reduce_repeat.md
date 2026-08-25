---
type: API
title: ReduceRepeat
description: 对每个repeat内所有数据进行归约操作，支持求和、求最大值和求最小值，可返回最值索引。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/reduction_compute/ReduceRepeat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# ReduceRepeat

对每个repeat内所有数据进行归约操作，支持求和、求最大值和求最小值，可返回最值索引。

本接口用于在矢量计算时设置mask。 - 当模板参数isSetMask = false时，推荐使用本接口。使用前需要先调用SetMaskCount/SetMaskNorm手动设置Mask模式，并通过调用本接口设置Counter/Normal模式下的mask。在不同的模式下，mask的含义不同： - Normal模式下，mask参数用来控制单次迭代内参与计算的元素个数。此时又可以划分为如下两种模式： - 连续模式：表示前面连续的多少个元素参与计算。取值范围和操作数的数据类型有关，数据类型不同，每次迭代内能够处理的元素个数最大值不同。当操作数为16位时，mask∈[0, 128]；当操作数为32位时，mask∈[0, 64]；当操作数为64位时，mask∈[0, 32]。 - 逐比特模式：可以按位控制哪些元素参与计算，bit位的值为1表示参与计算，0表示不参与。分为maskHigh

本接口组包含 高维切分, SetVectorMask, LocalTensor, LocalTensor, 掩码概述。

本接口属于 UB 矢量计算归约接口。

约束：该接口仅在矢量计算API的isSetMask模板参数为false时生效，使用完成后需要使用ResetMask将mask恢复为默认值。；针对Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品，mask = 0表示指令不会执行计算操作，该接口将被视为NOP（空操作）。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品 AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [选择低延迟指令，优化归约操作性能](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/low_latency_instruction.md)（`explains`）：指南的二分累加方案在数据缩到一个 repeat 后用 ReduceRepeat 收尾，并给出其相对 Add 和 ReduceSum 的延迟位置。
- [AscRepeatReduceMin](../../../c_api/vector_compute/asc_repeat_reduce_min.md)（`related`）：C++ ReduceRepeat 是同类重复规约的基础 API，补充 mask 和 repeat 语义，可与 C API 签名相互映射。
- [GetReduceRepeatMaxMinSpr](../reduction_compute_aux_config/get_reduce_repeat_max_min_spr_isasi.md)（`related`）：GetReduceRepeatMaxMinSpr 负责“获取ReduceRepeat或ReduceMax/ReduceMin计算的最值及索引，结果以全局变量形式存储”；ReduceRepeat 负责“对每个repeat内所有数据进行归约操作，支持求和、求最大值和求最小值，可返回最值索引”。
- [GetReduceRepeatSumSpr](../reduction_compute_aux_config/get_reduce_repeat_sum_spr_isasi.md)（`related`）：读取 Sum SPR 可核对 ReduceRepeat 的分 repeat 结果。
- [ReduceDataBlock](reduce_data_block.md)（`related`）：DataBlock 归约粒度小于 per-repeat，按输出粒度选择。
- [ReduceSum](reduce_sum.md)（`related`）：ReduceSum 跨有效输入求单结果，ReduceRepeat 保留每 repeat 结果。
- [AscRepeatReduceSum](../../../c_api/vector_compute/asc_repeat_reduce_sum.md)（`same_topic`）：ReduceRepeat 的 SUM 模式与 AscRepeatReduceSum 都对每个 Repeat 内的数据做二叉树求和；前者是可选 SUM/MAX/MIN 的基础 API，后者是 C API 的求和专用入口。
- [ReduceMin](reduce_min.md)（`same_topic`）：ReduceMin 与《ReduceRepeat》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
<!-- cannbot:related:end -->
