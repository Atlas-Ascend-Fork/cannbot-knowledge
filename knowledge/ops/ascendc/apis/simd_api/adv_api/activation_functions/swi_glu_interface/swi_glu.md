---
type: API
title: SwiGLU
description: 采用Swish作为激活函数的GLU变体，按元素对两源Tensor和标量参数计算SwiGLU结果
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SwiGLU_interface/SwiGLU.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SwiGLU

SwiGLU是采用Swish作为激活函数的GLU变体。 其中Swish激活函数的计算公式如下：β为常量
函数原型：
template <typename T, bool isReuseSource = false>
__aicore__ inline void SwiGLU(LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor0, const LocalTensor<T>& srcTensor1, const float& scalarValue, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t calCount)

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isReuseSource：是否允许修改源操作数。该参数预留，传入默认值false即可。
- dstTensor（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- srcTensor0/srcTensor1（输入）：源操作数。 源操作数的数据类型需要与目的操作数保持一致。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- scalarValue（输入）：激活函数中的β参数。

约束：
- 操作数地址对齐要求请参见通用地址对齐约束。
- 不支持源操作数与目的操作数地址重叠。
- 当前仅支持ND格式的输入，不支持其他格式。
- 不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [SwiGLU 高级 API 在非32B对齐 slice 上精度失败](../../../../../runbooks/precision/swiglu_adv_api_fails_non_32b_aligned_slice.md)（`exemplifies`）：Runbook 对 SwiGLU API 做了对齐/非对齐 slice A/B：32B 对齐 case 通过，非对齐 case 出现大错和 65504，回退手写链后 20/20；这是接口卡未写出的已验证输入边界。
- [GetSwiGLUMaxMinTmpSize](get_swi_glu_max_min_tmp_size.md)（`same_topic`）：SwiGLU 与《GetSwiGLUMaxMinTmpSize》的实质衔接是：SwiGLU 的 kernel、两种临时空间查询与非 32B slice 精度故障共同约束调用和缓冲区分配。
- [GetSwiGLUTmpBufferFactorSize](get_swi_glu_tmp_buffer_factor_size.md)（`same_topic`）：SwiGLU 与《GetSwiGLUTmpBufferFactorSize》的实质衔接是：SwiGLU 的 kernel、两种临时空间查询与非 32B slice 精度故障共同约束调用和缓冲区分配。
- [SwiGLU接口](swi_glu_interface.md)（`same_topic`）：SwiGLU 与《SwiGLU接口》的实质衔接是：SwiGLU 的 kernel、两种临时空间查询与非 32B slice 精度故障共同约束调用和缓冲区分配。
<!-- cannbot:related:end -->
