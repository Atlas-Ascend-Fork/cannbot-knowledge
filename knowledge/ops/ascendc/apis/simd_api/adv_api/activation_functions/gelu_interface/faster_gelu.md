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
