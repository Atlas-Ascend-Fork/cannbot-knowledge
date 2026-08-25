---
type: API
title: ReGlu
description: ReGlu是一种GLU变体，使用Relu作为激活函数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/ReGlu_interface/ReGlu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# ReGlu

ReGlu是一种GLU变体，使用Relu作为激活函数，计算公式如下： 其中Relu激活函数的计算公式如下：

函数原型：
template <typename T, bool isReuseSource = false>
__aicore__ inline void ReGlu(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor0, const LocalTensor<T>& srcTensor1, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t calCount)

参数：
- T：操作数的数据类型。不同型号支持的数据类型请参考[支持的数据类型](#li356910105419)。
- isReuseSource：是否允许修改源操作数。该参数预留，传入默认值false即可。
- dstTensor（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- srcTensor0（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 源操作数的数据类型需要与目的操作数保持一致。
- srcTensor1（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 源操作数的数据类型需要与目的操作数保持一致。

约束：
- 操作数地址对齐要求请参见通用地址对齐约束。
- 不支持源操作数与目的操作数地址重叠。
- 不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。
- 当前仅支持ND格式的输入，不支持其他格式。
- 支持的数据类型 Ascend 950PR/Ascend 950DT，支持的数据类型为：half、bfloat16_t、float。 Atlas A3 训练系列产品/Atlas A3 推理系列产品，支持的数据类型为：half、bfloat16_t、float。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetReGluMaxMinTmpSize](get_re_glu_max_min_tmp_size.md)（`related`）：GetReGluMaxMinTmpSize 与《ReGlu》的实质衔接是：host 侧临时空间上下限必须与 ReGlu kernel 的 sharedTmpBuffer 和复用源空间参数一致，接口页给出实际调用端。
- [Relu](../../../basic_api/memory_vector_compute/basic_arithmetic/relu.md)（`related`）：ReGlu 的门控分支使用 ReLU 激活；基础 Relu 明确 dst=max(0,src)，可用于拆解和验证 ReGlu 的激活部分。
- [ReGlu接口](re_glu_interface.md)（`same_topic`）：《ReGlu》明确“ReGlu是一种GLU变体，使用Relu作为激活函数。”；它与《ReGlu接口》的“提供ReGlu激活函数接口及GetReGluMaxMinTmpSize等Tiling临时空间大小查询接口。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
