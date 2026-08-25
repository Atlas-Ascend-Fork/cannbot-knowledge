---
type: API
title: ReduceSum
description: 对所有输入数据进行求和操作。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/reduction_compute/ReduceSum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# ReduceSum

对所有输入数据进行求和操作。

本接口用于在矢量计算时设置mask。 - 当模板参数isSetMask = false时，推荐使用本接口。使用前需要先调用SetMaskCount/SetMaskNorm手动设置Mask模式，并通过调用本接口设置Counter/Normal模式下的mask。在不同的模式下，mask的含义不同： - Normal模式下，mask参数用来控制单次迭代内参与计算的元素个数。此时又可以划分为如下两种模式： - 连续模式：表示前面连续的多少个元素参与计算。取值范围和操作数的数据类型有关，数据类型不同，每次迭代内能够处理的元素个数最大值不同。当操作数为16位时，mask∈[0, 128]；当操作数为32位时，mask∈[0, 64]；当操作数为64位时，mask∈[0, 32]。 - 逐比特模式：可以按位控制哪些元素参与计算，bit位的值为1表示参与计算，0表示不参与。分为maskHigh

本接口组包含 SetVectorMask, LocalTensor, LocalTensor, LocalTensor, 连续计算。

本接口属于 UB 矢量计算归约接口。

约束：该接口仅在矢量计算API的isSetMask模板参数为false时生效，使用完成后需要使用ResetMask将mask恢复为默认值。；针对Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品，mask = 0表示指令不会执行计算操作，该接口将被视为NOP（空操作）。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品 AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 ReduceSum AR 多行归约逐行错](../../../../../runbooks/precision/ascend950_reduce_sum_ar_multibundle_use_per_row.md)（`exemplifies`）：《Ascend950 ReduceSum AR 多行归约逐行错》说明Ascend950 上 ReduceSum<AR> 单次传入 aBundle>1 行时逐行结果错（总量近似但逐元素偏）；改逐行调用 ReduceSum(aBundle=1) 规避。仅当 aBundle>1 才触发。；《ReduceSum》说明对所有输入数据进行求和操作。。二者在该故障专指ReduceSum AR一次处理多行时逐行错误，逐行调用、跨chunk累加和归约边界是直接修复/验证点上存在可执行的直接衔接。
- [Reduce count 必须排除 DMA 对齐填充元素](../../../../../runbooks/precision/reduction_count_excludes_dma_padding.md)（`exemplifies`）：Reduce count 必须排除 DMA 对齐填充元素 与《ReduceSum》的实质衔接是：DMA 对齐容量不是 Reduce 的数学 count；DataCopyPad/padding 故障、Softmax 与 ReduceMax/Sum 各层入口共同验证填充零经 Exp 后会污染分母。
- [SoftmaxV2 ARA与AR模板R向累加树不同致1ULP分歧](../../../../../runbooks/precision/softmaxv2_ara_ar_r_1ulp.md)（`exemplifies`）：该 API 是 AR 模板段内硬件归约所用接口；与本卡读取到的 ARA 软件二分树对照，可定位两条实现链的合并节点不同。
- [int32 fp32累加reduce binary_equal不可达](../../../../../runbooks/precision/int32_fp32_reduce_binary_equal.md)（`exemplifies`）：《int32 fp32累加reduce binary_equal不可达》的任务是“int32 输入的 reduce 类算子内部 cast 到 fp32 累加，kernel 的 ReduceSum+bisection cache tree 与 golden 的 pairwise 折半是两棵不同 reduce 树；sum 超过 fp32 精确整数范围 2^24 时舍入路径不同致 1 ULP 差，cast 回 int32 后 bitwise 不一致，binary_equal 永不可达。”。《ReduceSum》具体提供“对所有输入数据进行求和操作。”，它直接用于int32→fp32 ReduceSum 的规约树、有效 count 和 2^24 舍入边界。
- [AscPairReduceSum](../../../c_api/vector_compute/asc_pair_reduce_sum.md)（`related`）：PairReduceSum 只完成一层相邻元素折叠，完整标量求和还需继续规约，ReduceSum 描述最终归约能力。
- [AscRepeatReduceSum](../../../c_api/vector_compute/asc_repeat_reduce_sum.md)（`related`）：Memory 基础 API ReduceSum 对整个输入做求和并提供 mask 管理，适合与 C API 的逐 Repeat 归约比较接口层和聚合范围。
- [GetReduceRepeatSumSpr](../reduction_compute_aux_config/get_reduce_repeat_sum_spr_isasi.md)（`related`）：GetReduceRepeatSumSpr 与《ReduceSum》的实质衔接是：GetReduceRepeatSumSpr 只读取前 n 连续 ReduceSum 的全局结果；ReduceSum 调用、临时空间和逐行/多 bundle 归约故障直接约束其使用。
- [Reduce](../../reg_vector_compute/reduction_compute/reduce.md)（`related`）：Reg::Reduce 的 SUM 与 ReduceSum 都完成向量求和归约，但分别面向寄存器编程和 LocalTensor 内存向量接口。
- [ReduceRepeat](reduce_repeat.md)（`related`）：ReduceSum 跨有效输入求单结果，ReduceRepeat 保留每 repeat 结果。
- [ReduceSum](../../../adv_api/reduction_operations/reduce_sum_interface/reduce_sum.md)（`related`）：Basic API ReduceSum 提供底层 UB 归约，高阶 ReduceSum 封装 shape/临时空间处理；二者解决同一求和归约但调用合同不同。
- [ReduceSum接口](../../../adv_api/reduction_operations/reduce_sum_interface/reduce_sum_interface.md)（`related`）：基础 Tensor ReduceSum 提供更低层归约，可按 shape 支持和临时空间需求与高阶接口选型。
- [AscDatablockReduceSum](../../../c_api/vector_compute/asc_datablock_reduce_sum.md)（`same_topic`）：AscDatablockReduceSum 与《ReduceSum》的实质衔接是：AscDatablockReduceSum 与 max/min、Reg datablock、repeat 和基础 ReduceDataBlock 共享数据块归约契约；GetDataBlockSizeInBytes 决定一次数据块所覆盖的有效元素。
- [AscReduceSum](../../../c_api/reg/reduce_compute/asc_reduce_sum.md)（`same_topic`）：Memory ReduceSum 与 AscReduceSum 都实现求和归约，后者在寄存器 C API 中显式接受 mask；该边对齐同一归约语义的两层接口。
<!-- cannbot:related:end -->
