---
type: API
title: FasterGeluV2
description: GELU激活函数FastGeluV2版本实现，通过公式化简降低算力需求，支持高精度和高性能模式。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/Gelu_interface/FasterGeluV2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# FasterGeluV2

在神经网络中，GELU是一个重要的激活函数，其灵感来源于relu和dropout，在激活中引入了随机正则的思想。为了降低GELU的算力需求，业界提出了FastGeluV2版本。本接口实现了FastGeluV2，计算公式如下： 其中，

函数原型：
template <typename T, bool highPrecision = false, bool highPerformance = false>
__aicore__ inline void FasterGeluV2(const LocalTensor<T>& dstLocal, const LocalTensor<T>& srcLocal, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t dataSize)

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

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Gelu](gelu.md)（`related`）：需要标准 GELU 数值语义时应使用 Gelu 而非更快近似。
- [GetGeluMaxMinTmpSize](get_gelu_max_min_tmp_size.md)（`related`）：V2 计算仍需按接口要求配置临时空间，不能沿用零 workspace 假设。
- [FasterGelu](faster_gelu.md)（`same_topic`）：FasterGelu 与 V2 共享相同 Tensor、临时空间、精度/性能模板开关和地址约束，但实现的是两套不同 FastGELU 化简式；选型时需按目标公式确认版本。
- [Gelu接口](gelu_interface.md)（`same_topic`）：总页给出精确 Gelu、FasterGelu 和 V2 的选型及 workspace 流程。
<!-- cannbot:related:end -->
