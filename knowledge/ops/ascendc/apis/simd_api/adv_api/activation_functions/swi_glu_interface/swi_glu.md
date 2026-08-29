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

- [SwiGLU 高级 API 在非32B对齐 slice 上精度失败](../../../../../runbooks/precision/swiglu_adv_api_fails_non_32b_aligned_slice.md)（`exemplifies`）：“**banned**：slice*sizeof(T) 非 32B 整数倍时禁用 `AscendC::SwiGLU` adv_api，必须回退手写 SiLU 链。”记录该接口在 dav-2201 非对齐 slice 上的实测失败边界；“操作数地址对齐要求请参见通用地址对齐约束。”是接口卡要求调用者核对的地址合同。
- [GetSwiGLUMaxMinTmpSize](get_swi_glu_max_min_tmp_size.md)（`related`）：“kernel侧SwiGLU接口的计算需要开发者预留 申请临时空间，本接口用于在host侧获取预留 申请的最大最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。”；“__aicore__ inline void SwiGLU(LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor0, const LocalTensor<T>& srcTensor1, const float& scalarValue, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t calCount)”。Host 查询得到的空间范围直接决定 SwiGLU kernel 的 sharedTmpBuffer 申请。
- [GetSwiGLUTmpBufferFactorSize](get_swi_glu_tmp_buffer_factor_size.md)（`related`）：“__aicore__ inline void SwiGLU(LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor0, const LocalTensor<T>& srcTensor1, const float& scalarValue, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t calCount)”与“kernel侧SwiGLU接口的计算需要开发者预留 申请临时空间，最大临时空间（maxTmpBuffer）和输入所占空间（inputSize * typeSize）存在以下关系： maxTmpBuffer = maxLiveNodeCount * inputSize * typeSize + extraBuffer 其中maxLiveNodeCount表示最大临时空间是输入所占空间的多少倍；extraBuffer表示使用的额外临时空间大小。”提供双方正文证据。SwiGLU 原型要求 sharedTmpBuffer，helper 给出 maxLiveNodeCount 与 extraBuffer 计算该缓冲区容量，构成实际调用前的空间准备。
- [grouped_matmul_swiglu_quant A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_swiglu_quant.md)（`related`）：随后把 `C_e［:,0:N/2］` 作为第一分支、`C_e［:,N/2:N］` 作为第二分支，源码调用 `SwiGLU(src0=后半, src1=前半, beta=1)`；A4W4 再乘逐专家或逐通道 `smoothScale`。；SwiGLU是采用Swish作为激活函数的GLU变体。 其中Swish激活函数的计算公式如下：β为常量。算子卡的双分支参数顺序与 beta=1 直接落到 SwiGLU API 合同。
<!-- cannbot:related:end -->
