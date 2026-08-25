---
type: API
title: Gelu
description: GELU激活函数实现，灵感来源于Relu和Dropout，在激活中引入随机正则思想，支持高精度和高性能模式。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/Gelu_interface/Gelu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Gelu

在神经网络中，GELU是一个重要的激活函数，其灵感来源于Relu和Dropout，在激活中引入了随机正则的思想。计算公式如下： ，化简后可得

函数原型：
template <typename T, bool highPrecision = false, bool highPerformance = false>
__aicore__ inline void Gelu(const LocalTensor<T>& dstLocal, const LocalTensor<T>& srcLocal, const uint32_t dataSize)

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- highPrecision：是否开启高精度模式，以提升运算准确度。默认值为false，表示不开启高精度模式。 注意：高精度模式只在half数据类型下开启后生效，该参数的取值不影响float数据类型下的接口精度和性能。
- highPerformance：是否开启高性能模式，以提升运算效率。默认值为false，表示不开启高性能模式。 注意：开启高性能模式相比于默认不开启高精度和高性能模式会有精度下降，同时开启高精度和高性能模式相比于仅开启高性能模式可能会有性能下降。
- dstLocal（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- srcLocal（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 源操作数的数据类型需要与目的操作数保持一致。

约束：
- 源操作数和目的操作数的Tensor空间可以复用。
- 不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。
- 操作数地址对齐要求请参见通用地址对齐约束。
- 仅支持输入shape为ND格式。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 Reg 命名空间无 Erf/Tanh 封装](../../../../../runbooks/compilation/ascend950_reg_erf_tanh.md)（`exemplifies`）：Ascend950 Reg 命名空间无 Erf/Tanh 封装 与《Gelu》的实质衔接是：Ascend950 Reg 无 Erf/Tanh 封装时需用可用 Exp/Log/基础算术组合或高阶/SIMT 接口替代，并验证数值稳定性。
- [AscendC GELU 三系数 erfc 在大值域 fp32 精度不足](../../../../../runbooks/precision/gelu_erfc_polynomial_precision_budget.md)（`exemplifies`）：Gelu 与《AscendC GELU 三系数 erfc 在大值域 fp32 精度不足》的实质衔接是：Gelu 接口、快速近似变体和空间查询共同定义高精度/高性能调用；GeGLU 直接以 GELU 为门控，两个 runbook 给出 erfc 近似与负尾相消的可执行精度边界。
- [GELU 负尾部用 erfc 形态避免大数相消](../../../../../runbooks/precision/gelu_negative_tail_erfc_avoids_cancellation.md)（`exemplifies`）：Gelu 与《GELU 负尾部用 erfc 形态避免大数相消》的实质衔接是：Gelu 接口、快速近似变体和空间查询共同定义高精度/高性能调用；GeGLU 直接以 GELU 为门控，两个 runbook 给出 erfc 近似与负尾相消的可执行精度边界。
- [中级性能优化](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/gelu_reg_vector_operator/intermediate_optimization.md)（`explains`）：中级性能优化 与《Gelu》的实质衔接是：GELU 中级优化从入门版迁到 Reg/VF 融合并使用 Load/Store/PipeBarrier；所选故障卡直接约束这些调用和 GELU 数值实现。
- [FasterGeluV2](faster_gelu_v2.md)（`related`）：需要标准 GELU 数值语义时应使用 Gelu 而非更快近似。
- [GeGLU](../ge_glu_interface/ge_glu.md)（`related`）：Gelu 与《GeGLU》的实质衔接是：Gelu 接口、快速近似变体和空间查询共同定义高精度/高性能调用；GeGLU 直接以 GELU 为门控，两个 runbook 给出 erfc 近似与负尾相消的可执行精度边界。
- [FasterGelu](faster_gelu.md)（`same_topic`）：Gelu 与《FasterGelu》的实质衔接是：Gelu 接口、快速近似变体和空间查询共同定义高精度/高性能调用；GeGLU 直接以 GELU 为门控，两个 runbook 给出 erfc 近似与负尾相消的可执行精度边界。
- [Gelu接口](gelu_interface.md)（`same_topic`）：Gelu 与《Gelu接口》的实质衔接是：Gelu 接口、快速近似变体和空间查询共同定义高精度/高性能调用；GeGLU 直接以 GELU 为门控，两个 runbook 给出 erfc 近似与负尾相消的可执行精度边界。
- [GetGeluMaxMinTmpSize](get_gelu_max_min_tmp_size.md)（`same_topic`）：Gelu 与《GetGeluMaxMinTmpSize》的实质衔接是：Gelu 接口、快速近似变体和空间查询共同定义高精度/高性能调用；GeGLU 直接以 GELU 为门控，两个 runbook 给出 erfc 近似与负尾相消的可执行精度边界。
<!-- cannbot:related:end -->
