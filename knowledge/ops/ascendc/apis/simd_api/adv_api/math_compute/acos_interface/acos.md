---
type: API
title: Acos
description: 按元素做反余弦函数计算，输入值域需在-1到1范围内
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Acos_interface/Acos.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# Acos

按元素做反余弦函数计算，计算公式如下：

函数原型：
template <typename T, bool isReuseSource = false>
__aicore__ inline void Acos(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t calCount)

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isReuseSource：是否允许修改源操作数。该参数预留，传入默认值false即可。
- dstTensor（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- srcTensor（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 源操作数的数据类型需要与目的操作数保持一致。
- sharedTmpBuffer（输入）：临时缓存。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 用于Acos内部复杂计算时存储中间变量，由开发者提供。 临时空间大小BufferSize的获取方式请参考GetAcosMaxMinTmpSize。

约束：
- 输入源数据需保持值域在[-1, 1]。若输入不在范围内，输出结果无效。
- 不支持源操作数与目的操作数地址重叠。
- 不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。
- 操作数地址对齐要求请参见通用地址对齐约束。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetAcosMaxMinTmpSize](get_acos_max_min_tmp_size.md)（`related`）：GetAcosMaxMinTmpSize 与《Acos》的实质衔接是：Acos 的 host 临时空间查询必须与 kernel Acos、接口封装及 factor-size 推算使用同一 shape/typeSize/复用策略。
- [GetAcosTmpBufferFactorSize](get_acos_tmp_buffer_factor_size.md)（`related`）：当已有固定临时空间预算时，GetAcosTmpBufferFactorSize 可反推 Acos 单次可处理元素量，补足容量受限时的 tiling 决策。
- [Acos接口](acos_interface.md)（`same_topic`）：Acos接口 的核心契约是“提供Acos反余弦计算接口及其Tiling临时空间大小查询接口，包含Acos、GetAcosMaxMinTmpSize等”；Acos 补充“按元素做反余弦函数计算，输入值域需在-1到1范围内”。
<!-- cannbot:related:end -->
