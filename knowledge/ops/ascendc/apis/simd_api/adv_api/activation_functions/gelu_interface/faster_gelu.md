---
type: API
title: FasterGelu
description: GELU激活函数的FastGelu化简版本，通过公式化简大幅提升计算性能，支持高精度和高性能模式。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/Gelu_interface/FasterGelu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# FasterGelu

在神经网络中，GELU是一个重要的激活函数，其灵感来源于relu和dropout，在激活中引入了随机正则的思想。为了降低GELU的算力需求，业界提出了FastGelu等版本。本接口FasterGelu是针对FastGelu的化简版本，公式化简可以大幅度提升计算性能。计算公式如下: ，化简后可得

函数原型：
template <typename T, bool highPrecision = false, bool highPerformance = false>
__aicore__ inline void FasterGelu(const LocalTensor<T>& dstLocal, const LocalTensor<T>& srcLocal, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t dataSize)

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- highPrecision：是否开启高精度模式，以提升运算准确度。默认值为false，表示不开启高精度模式。 注意：高精度模式只在half数据类型下开启后生效，该参数的取值不影响float数据类型下的接口精度和性能。
- highPerformance：是否开启高性能模式，以提升运算效率。默认值为false，表示不开启高性能模式。 注意：开启高性能模式相比于默认不开启高精度和高性能模式会有精度下降，同时开启高精度和高性能模式相比于仅开启高性能模式可能会有性能下降。
- dstLocal（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- srcLocal（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 源操作数的数据类型需要与目的操作数保持一致。

约束：
- 源操作数和目的操作数的Tensor空间可以复用。
- 操作数地址对齐要求请参见通用地址对齐约束。
- 当前仅支持ND格式的输入，不支持其他格式。
- 不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetGeluMaxMinTmpSize](get_gelu_max_min_tmp_size.md)（`related`）：FasterGelu 的 sharedTmpBuffer 由 Host 侧 GetGeluMaxMinTmpSize 按 shape 与 typeSize 给出合法上下界，最小值决定正确性、区间内增大空间可换取性能。
- [FasterGeluV2](faster_gelu_v2.md)（`same_topic`）：FasterGelu 与 V2 共享相同 Tensor、临时空间、精度/性能模板开关和地址约束，但实现的是两套不同 FastGELU 化简式；选型时需按目标公式确认版本。
- [Gelu](gelu.md)（`same_topic`）：Gelu 与《FasterGelu》的实质衔接是：Gelu 接口、快速近似变体和空间查询共同定义高精度/高性能调用；GeGLU 直接以 GELU 为门控，两个 runbook 给出 erfc 近似与负尾相消的可执行精度边界。
<!-- cannbot:related:end -->
