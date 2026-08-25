---
type: API
title: MulAddDst
description: 按元素将src0和src1相乘并和dst相加，将最终结果存放进dst中。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.composite]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/composite_compute/MulAddDst.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# MulAddDst

按元素将src0和src1相乘并和dst相加，将最终结果存放进dst中。

本接口用于在矢量计算时设置mask。 - 当模板参数isSetMask = false时，推荐使用本接口。使用前需要先调用SetMaskCount/SetMaskNorm手动设置Mask模式，并通过调用本接口设置Counter/Normal模式下的mask。在不同的模式下，mask的含义不同： - Normal模式下，mask参数用来控制单次迭代内参与计算的元素个数。此时又可以划分为如下两种模式： - 连续模式：表示前面连续的多少个元素参与计算。取值范围和操作数的数据类型有关，数据类型不同，每次迭代内能够处理的元素个数最大值不同。当操作数为16位时，mask∈[0, 128]；当操作数为32位时，mask∈[0, 64]；当操作数为64位时，mask∈[0, 32]。 - 逐比特模式：可以按位控制哪些元素参与计算，bit位的值为1表示参与计算，0表示不参与。分为maskHigh

本接口组包含 SetVectorMask, LocalTensor, 连续计算, 掩码操作, 高维切分。

本接口属于 UB 矢量计算复合算术接口，组合多个基础运算。

约束：该接口仅在矢量计算API的isSetMask模板参数为false时生效，使用完成后需要使用ResetMask将mask恢复为默认值。；针对Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品，mask = 0表示指令不会执行计算操作，该接口将被视为NOP（空操作）。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品 AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [MulAddDst FMA 单次舍入与 golden Mul+Add 双舍入偏差](../../../../../runbooks/precision/muladddst_fma_golden_mul_add.md)（`exemplifies`）：该实测卡说明 Reg MulAddDst 采用单次舍入 FMA，而 golden 的分离 Mul+Add 是双舍入，能直接解释使用本乘加语义时的 1 ULP 误差。
- [advance_step in-place kernel FATBIN wrap](../../../../../runbooks/compilation/fatbin_wrapper_param_count_matches_opdef_input_plus_output.md)（`exemplifies`）：本卡的 in-place 输出复用语义可由 MulAddDst 这类显式 dst 累加接口对照，但 wrapper 形参数仍必须保留声明的 output。
- [AscMulAdd](../../../c_api/vector_compute/asc_mul_add.md)（`related`）：MulAddDst 明确给出 dst=src0*src1+dst 的累加语义，是理解 AscMulAdd 目的缓冲既作输入又作输出的对应接口。
- [FusedMulAdd](fused_mul_add.md)（`related`）：两接口都是乘加复合操作，但分别计算 dst=src0*dst+src1 与 dst=src0*src1+dst，可按累加操作数位置选型。
- [MulAddDst](../../reg_vector_compute/composite_compute/mul_add_dst.md)（`related`）：Reg MulAddDst 与 Memory API 都实现 dst=src0*src1+dst；前者揭示寄存器级 FMA 路径，后者在 UB Tensor 上暴露 mask/repeat 约束。
- [MulAddRelu](mul_add_relu.md)（`same_topic`）：MulAddRelu 与《MulAddDst》的实质衔接是：MulAddRelu 的 C API 和 MulAddDst 共享乘加复合语义；FMA 舍入卡说明合并乘加与分步 golden 的可见差异。
- [MulDstAdd](../../reg_vector_compute/composite_compute/mul_dst_add.md)（`same_topic`）：MulDstAdd 与《MulAddDst》的衔接是：MulDstAdd 与 MulAddDst 共享乘加写回但目标操作数位置不同；ZEROING trait 是 focal 明确允许的掩码模式，错误沿用累加式 mask 会改变写回结果。
<!-- cannbot:related:end -->
