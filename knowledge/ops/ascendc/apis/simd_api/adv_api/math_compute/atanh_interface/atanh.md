---
type: API
title: Atanh
description: 按元素做反双曲正切函数计算，输入值域需在指定区间内
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Atanh_interface/Atanh.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# Atanh

按元素做反双曲正切余弦函数计算，计算公式如下：

函数原型：
template <typename T, bool isReuseSource = false>
__aicore__ inline void Atanh(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t calCount)

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isReuseSource：是否允许修改源操作数。该参数预留，传入默认值false即可。
- dstTensor（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- srcTensor（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 源操作数的数据类型需要与目的操作数保持一致。
- sharedTmpBuffer（输入）：临时缓存。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 用于Atanh内部复杂计算时存储中间变量，由开发者提供。 临时空间大小BufferSize的获取方式请参考GetAtanhMaxMinTmpSize。

约束：
- 输入源数据需保持值域在(-0.99，-0.001)或者(0.001， 0.99)区间内。若输入不在范围内，输出结果无效。
- 不支持源操作数与目的操作数地址重叠。
- 不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。
- 操作数地址对齐要求请参见通用地址对齐约束。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Atanhf](../../../../simt_api/math_functions/float_math_functions/atanhf.md)（`same_topic`）：《Atanh》处理“按元素做反双曲正切函数计算，输入值域需在指定区间内”。《Atanhf》提供“获取输入数据的反双曲正切值。”，其具体合同或探针直接接入Atanh Kernel 调用、临时空间推导和 SIMT 对应实现。
- [Atanh接口](atanh_interface.md)（`same_topic`）：《Atanh》处理“按元素做反双曲正切函数计算，输入值域需在指定区间内”。《Atanh接口》提供“提供Atanh反双曲正切计算接口及其Tiling临时空间大小查询接口，包含Atanh、GetAtanhMaxMinTmpSize等。”，其具体合同或探针直接接入Atanh Kernel 调用、临时空间推导和 SIMT 对应实现。
- [GetAtanhMaxMinTmpSize](get_atanh_max_min_tmp_size.md)（`same_topic`）：《Atanh》处理“按元素做反双曲正切函数计算，输入值域需在指定区间内”。《GetAtanhMaxMinTmpSize》提供“在host侧获取Atanh接口预留临时空间的最大和最小值，用于Tiling参数选择”，其具体合同或探针直接接入Atanh Kernel 调用、临时空间推导和 SIMT 对应实现。
- [GetAtanhTmpBufferFactorSize](get_atanh_tmp_buffer_factor_size.md)（`same_topic`）：《Atanh》处理“按元素做反双曲正切函数计算，输入值域需在指定区间内”。《GetAtanhTmpBufferFactorSize》提供“获取Atanh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数”，其具体合同或探针直接接入Atanh Kernel 调用、临时空间推导和 SIMT 对应实现。
<!-- cannbot:related:end -->
