---
type: API
title: Atan
description: 按元素做反正切运算，支持泰勒展开和多项式逼近两种算法配置
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Atan_interface/Atan.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Atan

按元素做三角函数反正切运算，计算公式如下：

函数原型：
template <typename T, bool isReuseSource = false, const AtanConfig& config = defaultAtanConfig>
__aicore__ inline void Atan(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t calCount)

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isReuseSource：是否允许修改源操作数。该参数预留，传入默认值false即可。
- config：Atan算法的相关配置。此参数可选配，AtanConfig类型，具体定义如下方代码所示，其中参数的含义为：algo：Atan内部实现使用的算法。AtanAlgo类型，支持的取值如下：TAYLOR_EXPANSION：默认值。该算法使用6阶泰勒展开实现Atan，支持的数据类型为half、float。POLYNOMIAL_APPROXIMATION：该算法是17次多项式逼近算法，支持的数据类型为float。
- dstTensor（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- srcTensor（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 源操作数的数据类型需要与目的操作数保持一致。

约束：
- 不支持源操作数与目的操作数地址重叠。
- 不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。
- 操作数地址对齐要求请参见通用地址对齐约束。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetAtanMaxMinTmpSize](get_atan_max_min_tmp_size.md)（`related`）：不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；kernel侧Atan接口的计算需要开发者预留 申请临时空间。左卡的 Atan Kernel 需要独立 sharedTmpBuffer，右卡在 Host 侧按 shape、dtype 与复用配置给出其合法空间范围；右卡结果直接决定左卡缓冲区的申请大小。
- [GetAtanTmpBufferFactorSize](get_atan_tmp_buffer_factor_size.md)（`related`）：该接口用于获取maxLiveNodeCount和extraBuf，在固定空间大小的情况下，通过maxLiveNodeCount和extraBuf可以推算算子单次最大计算元素数量。；template <typename T, bool isReuseSource = false, const AtanConfig& config = defaultAtanConfig> __aicore__ inline void Atan(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t calCount)；Host 侧系数用于反推单次元素上限，恰好约束带 sharedTmpBuffer 与 calCount 的 Atan 重载如何切分计算。
<!-- cannbot:related:end -->
