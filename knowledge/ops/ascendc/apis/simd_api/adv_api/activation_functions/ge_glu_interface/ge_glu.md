---
type: API
title: GeGLU
description: 采用GELU作为激活函数的GLU变体，按元素对两源Tensor计算GeGLU结果
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/GeGLU_interface/GeGLU.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GeGLU

GeGLU是采用GELU作为激活函数的GLU变体。 其中GELU激活函数的计算公式如下： 上述公式中的erf为误差函数：

函数原型：
template <typename T, bool isReuseSource = false>
__aicore__ inline void GeGLU(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor0, const LocalTensor<T>& srcTensor1, const LocalTensor<uint8_t>& sharedTmpBuffer, uint32_t calCount)

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isReuseSource：是否允许修改源操作数。该参数预留，传入默认值false即可。
- dstTensor（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- srcTensor0 srcTensor1（输入）：源操作数。 源操作数的数据类型需要与目的操作数保持一致。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- sharedTmpBuffer（输入）：临时缓存。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 用于GeGLU内部复杂计算时存储中间变量，由开发者提供。 临时空间大小BufferSize的获取方式请参考GetGeGLUMaxMinTmpSize。

约束：
- 操作数地址对齐要求请参见通用地址对齐约束。
- 不支持源操作数与目的操作数地址重叠。
- 当前仅支持ND格式的输入，不支持其他格式。
- 不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetGeGLUMaxMinTmpSize](get_ge_glu_max_min_tmp_size.md)（`related`）：kernel侧GeGLU接口的计算需要开发者预留 申请临时空间，本接口用于在host侧获取预留 申请的最大最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。；用于GeGLU内部复杂计算时存储中间变量，由开发者提供。 临时空间大小BufferSize的获取方式请参考GetGeGLUMaxMinTmpSize。；GeGLU 的 sharedTmpBuffer 大小明确由 Host 侧范围接口产生，形成 Tiling 参数到 kernel 临时缓存的直接合同。
<!-- cannbot:related:end -->
