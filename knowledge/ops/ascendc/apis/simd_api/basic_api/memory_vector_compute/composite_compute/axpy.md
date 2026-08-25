---
type: API
title: Axpy
description: 计算向量和标量的乘积，并将乘积结果逐元素加到的输出向量上。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.composite]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/composite_compute/Axpy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Axpy

计算向量和标量的乘积，并将乘积结果逐元素加到的输出向量上。

本接口用于在矢量计算时设置mask。 - 当模板参数isSetMask = false时，推荐使用本接口。使用前需要先调用SetMaskCount/SetMaskNorm手动设置Mask模式，并通过调用本接口设置Counter/Normal模式下的mask。在不同的模式下，mask的含义不同： - Normal模式下，mask参数用来控制单次迭代内参与计算的元素个数。此时又可以划分为如下两种模式： - 连续模式：表示前面连续的多少个元素参与计算。取值范围和操作数的数据类型有关，数据类型不同，每次迭代内能够处理的元素个数最大值不同。当操作数为16位时，mask∈[0, 128]；当操作数为32位时，mask∈[0, 64]；当操作数为64位时，mask∈[0, 32]。 - 逐比特模式：可以按位控制哪些元素参与计算，bit位的值为1表示参与计算，0表示不参与。分为maskHigh

本接口组包含 SetVectorMask, 连续计算, 掩码操作, 高维切分API, UnaryRepeatParams。

本接口属于 UB 矢量计算复合算术接口，组合多个基础运算。

约束：该接口仅在矢量计算API的isSetMask模板参数为false时生效，使用完成后需要使用ResetMask将mask恢复为默认值。；针对Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品，mask = 0表示指令不会执行计算操作，该接口将被视为NOP（空操作）。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品 AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AscAxpy](../../../c_api/vector_compute/asc_axpy.md)（`related`）：Axpy 与《AscAxpy》的实质衔接是：Axpy 把缩放源加到目的，需与高阶 Axpy、mask/repeat 和临时空间查询配套。
- [Axpy](../../../adv_api/math_compute/axpy_interface/axpy.md)（`related`）：Axpy 与《Axpy》的实质衔接是：Axpy 把缩放源加到目的，需与高阶 Axpy、mask/repeat 和临时空间查询配套。
- [Axpy接口](../../../adv_api/math_compute/axpy_interface/axpy_interface.md)（`related`）：基础 Axpy 与高阶 Axpy 都实现 y=a*x+y，但前者是直接复合矢量接口，后者显式管理临时空间并强调 Muls+Add 精度；可据空间和精度约束选层级。
- [AscAxpy](../../../c_api/reg/compound_compute/asc_axpy.md)（`same_topic`）：AscAxpy 与《Axpy》的衔接是：AscAxpy 的 C Vector、基础及高阶 Axpy 入口实现同一 alpha*x+y 数据流，差异集中在张量形态、临时空间和调度层级。
- [Axpy](../../reg_vector_compute/composite_compute/axpy.md)（`same_topic`）：Axpy说明计算向量和标量的乘积，并将乘积结果逐元素加到的输出向量上。
<!-- cannbot:related:end -->
