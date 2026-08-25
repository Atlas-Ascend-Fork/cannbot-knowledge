---
type: API
title: GetAtanhTmpBufferFactorSize
description: 获取Atanh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Atanh_interface/GetAtanhTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetAtanhTmpBufferFactorSize

kernel侧Atanh接口的计算需要开发者预留 申请临时空间，最大临时空间（maxTmpBuffer）和输入所占空间（inputSize * typeSize）存在以下关系： maxTmpBuffer = maxLiveNodeCount * inputSize * typeSize + extraBuffer 其中maxLiveNodeCount表示最大临时空间是输入所占空间的多少倍；extraBuffer表示使用的额外临时空间大小。

函数原型：void GetAtanhTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- maxLiveNodeCount（输出）：最大存活节点数，最大临时空间是输入所占空间的多少倍。
- extraBuf（输出）：使用的额外临时空间大小，单位为字节。

<!-- cannbot:related:start -->
## 相关

- [Atanhf](../../../../simt_api/math_functions/float_math_functions/atanhf.md)（`related`）：《GetAtanhTmpBufferFactorSize》处理“获取Atanh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数”。《Atanhf》明确“获取输入数据的反双曲正切值。”，可直接用于核对Atanh 高阶 Kernel 的临时空间系数、上下界估算和对应标量实现。
- [Atanh接口](atanh_interface.md)（`related`）：《GetAtanhTmpBufferFactorSize》处理“获取Atanh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数”。《Atanh接口》明确“提供Atanh反双曲正切计算接口及其Tiling临时空间大小查询接口，包含Atanh、GetAtanhMaxMinTmpSize等。”，可直接用于核对Atanh 高阶 Kernel 的临时空间系数、上下界估算和对应标量实现。
- [GetTanhTmpBufferFactorSize](../tanh_interface/get_tanh_tmp_buffer_factor_size.md)（`related`）：Atanh 是反函数且容量公式不同。
- [Atanh](atanh.md)（`same_topic`）：《Atanh》处理“按元素做反双曲正切函数计算，输入值域需在指定区间内”。《GetAtanhTmpBufferFactorSize》提供“获取Atanh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数”，其具体合同或探针直接接入Atanh Kernel 调用、临时空间推导和 SIMT 对应实现。
- [GetAtanhMaxMinTmpSize](get_atanh_max_min_tmp_size.md)（`same_topic`）：《GetAtanhTmpBufferFactorSize》处理“获取Atanh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数”。《GetAtanhMaxMinTmpSize》明确“在host侧获取Atanh接口预留临时空间的最大和最小值，用于Tiling参数选择”，可直接用于核对Atanh 高阶 Kernel 的临时空间系数、上下界估算和对应标量实现。
<!-- cannbot:related:end -->
