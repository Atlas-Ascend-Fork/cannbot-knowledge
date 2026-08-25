---
type: API
title: Asinh
description: 按元素做反双曲正弦函数计算，输入值域需在-65504到65504范围内
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Asinh_interface/Asinh.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# Asinh

按元素做反双曲正弦函数计算，计算公式如下：

函数原型：
template <typename T, bool isReuseSource = false>
__aicore__ inline void Asinh(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t calCount)

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isReuseSource：是否允许修改源操作数。该参数预留，传入默认值false即可。
- dstTensor（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- srcTensor（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 源操作数的数据类型需要与目的操作数保持一致。
- sharedTmpBuffer（输入）：临时缓存。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 用于Asinh内部复杂计算时存储中间变量，由开发者提供。 临时空间大小BufferSize的获取方式请参考GetAsinhMaxMinTmpSize。

约束：
- 输入源数据需保持值域在[-65504, 65504]。若输入不在范围内，输出结果无效。
- 不支持源操作数与目的操作数地址重叠。
- 不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。
- 操作数地址对齐要求请参见通用地址对齐约束。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetAsinhTmpBufferFactorSize](get_asinh_tmp_buffer_factor_size.md)（`related`）：The factor query supports deriving the maximum Asinh tile size from a fixed available workspace.
- [Asinhf](../../../../simt_api/math_functions/float_math_functions/asinhf.md)（`same_topic`）：高阶 Tensor Asinh 与 SIMT asinhf 完成同一反双曲正弦。
- [Asinh接口](asinh_interface.md)（`same_topic`）：《Asinh》明确“按元素做反双曲正弦函数计算，输入值域需在-65504到65504范围内”；它与《Asinh接口》的“提供Asinh反双曲正弦计算接口及其Tiling临时空间大小查询接口，包含Asinh、GetAsinhMaxMinTmpSize等。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetAsinhMaxMinTmpSize](get_asinh_max_min_tmp_size.md)（`same_topic`）：《GetAsinhMaxMinTmpSize》的任务是“在host侧获取Asinh接口预留临时空间的最大和最小值，用于Tiling参数选择”。《Asinh》具体提供“按元素做反双曲正弦函数计算，输入值域需在-65504到65504范围内”，它直接用于Asinh workspace 上下界和 factor 到 Kernel 的同一空间合同。
<!-- cannbot:related:end -->
