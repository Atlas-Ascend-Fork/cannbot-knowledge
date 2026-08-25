---
type: API
title: Acosh
description: 按元素做双曲反余弦函数计算，输入值域需在1到65504范围内
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Acosh_interface/Acosh.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# Acosh

按元素做双曲反余弦函数计算，计算公式如下：

函数原型：
template <typename T, bool isReuseSource = false>
__aicore__ inline void Acosh(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t calCount)

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isReuseSource：是否允许修改源操作数。该参数预留，传入默认值false即可。
- dstTensor（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- srcTensor（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 源操作数的数据类型需要与目的操作数保持一致。
- sharedTmpBuffer（输入）：临时缓存。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 用于Acosh内部复杂计算时存储中间变量，由开发者提供。 临时空间大小BufferSize的获取方式请参考GetAcoshMaxMinTmpSize。

约束：
- 输入源数据需保持值域在[1, 65504]。若输入不在范围内，输出结果无效。
- 不支持源操作数与目的操作数地址重叠。
- 不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。
- 操作数地址对齐要求请参见通用地址对齐约束。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetAcoshTmpBufferFactorSize](get_acosh_tmp_buffer_factor_size.md)（`related`）：《GetAcoshTmpBufferFactorSize》明确“获取Acosh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数”；它与《Acosh》的“按元素做双曲反余弦函数计算，输入值域需在1到65504范围内”在实际调用参数、数据流或结果校验上直接衔接。
- [Acoshf](../../../../simt_api/math_functions/float_math_functions/acoshf.md)（`same_topic`）：《Acoshf》明确“获取输入数据的双曲反余弦值。”；它与《Acosh》的“按元素做双曲反余弦函数计算，输入值域需在1到65504范围内”在实际调用参数、数据流或结果校验上直接衔接。
- [Acosh接口](acosh_interface.md)（`same_topic`）：《Acosh接口》明确“提供Acosh反双曲余弦计算接口及其Tiling临时空间大小查询接口，包含Acosh、GetAcoshMaxMinTmpSize等。”；它与《Acosh》的“按元素做双曲反余弦函数计算，输入值域需在1到65504范围内”在实际调用参数、数据流或结果校验上直接衔接。
- [GetAcoshMaxMinTmpSize](get_acosh_max_min_tmp_size.md)（`same_topic`）：Acosh 的 sharedTmpBuffer 明确引用本 Host 查询；查询的 minValue 是正确性下限，maxValue 以上空间不再被使用。
<!-- cannbot:related:end -->
