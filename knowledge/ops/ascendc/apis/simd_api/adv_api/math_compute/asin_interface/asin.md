---
type: API
title: Asin
description: 按元素做反正弦函数计算，输入值域需在-1到1范围内
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Asin_interface/Asin.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# Asin

按元素做反正弦函数计算，计算公式如下：

函数原型：
template <typename T, bool isReuseSource = false>
__aicore__ inline void Asin(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t calCount)

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isReuseSource：是否允许修改源操作数。该参数预留，传入默认值false即可。
- dstTensor（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- srcTensor（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 源操作数的数据类型需要与目的操作数保持一致。
- sharedTmpBuffer（输入）：临时缓存。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 用于Asin内部复杂计算时存储中间变量，由开发者提供。 临时空间大小BufferSize的获取方式请参考GetAsinMaxMinTmpSize。

约束：
- 输入源数据需保持值域在[-1, 1]。若输入不在范围内，输出结果无效。
- 不支持源操作数与目的操作数地址重叠。
- 不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。
- 操作数地址对齐要求请参见通用地址对齐约束。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetAsinMaxMinTmpSize](get_asin_max_min_tmp_size.md)（`related`）：临时空间大小BufferSize的获取方式请参考GetAsinMaxMinTmpSize。；本接口用于在host侧获取预留 申请的最大和最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。。Asin 明确把临时空间取得步骤交给右侧 Host 接口，右侧产生的范围又直接成为 Asin Kernel 的 Tiling 输入；两者是计算接口与资源查询 helper 的互补任务链，并非同一操作。
- [更多样例（数学计算）](../more_examples.md)（`related`）：样例一：展示GetXxxMaxMinTmpSize Tiling接口与kernel侧API配套使用。Host侧通过AscendC::TensorShape描述输入shape，调用GetXxxMaxMinTmpSize获取maxValue/minValue，结合PlatformAscendC获取UB剩余空间，选取合适的tmpSize写入tiling data；kernel侧读取tiling data分配临时空间并调用高阶API（以Asin为例）。；sharedTmpBuffer（输入）：临时缓存。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 用于Asin内部复杂计算时存储中间变量，由开发者提供。 临时空间大小BufferSize的获取方式请参考GetAsinMaxMinTmpSize。；API 页提供样例所消费的 Asin 临时空间参数合同。
<!-- cannbot:related:end -->
