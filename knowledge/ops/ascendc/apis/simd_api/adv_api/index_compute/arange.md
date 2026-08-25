---
type: API
title: Arange（索引计算）
description: 给定起始值，等差值和长度，返回一个等差数列。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.indexing]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/index_compute/Arange.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# Arange（索引计算）

给定起始值，等差值和长度，返回一个等差数列。

函数原型：
template <typename T>
__aicore__ inline void Arange(const LocalTensor<T>& dst, const T firstValue, const T diffValue, const int32_t count)

参数：
- T：操作数的数据类型。不同型号支持的数据类型请参考[支持的数据类型](#li73338460199)。
- dst（输出）：目的操作数。dst的大小应大于等于count * sizeof(T)。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- firstValue（输入）：等差数列的首个元素值。
- diffValue（输入）：等差数列元素之间的差值，应大于等于0。
- count（输入）：等差数列的长度。count>0。

约束：
- 当前仅支持ND格式的输入，不支持其他格式。
- 支持的数据类型 Ascend 950PR/Ascend 950DT，支持的数据类型为：int16_t、half、int32_t、float、int64_t。 Atlas A3 训练系列产品/Atlas A3 推理系列产品，支持的数据类型为：int16_t、half、int32_t、float。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetArangeMaxMinTmpSize](get_arange_max_min_tmp_size.md)（`related`）：Arange 的 sharedTmpBuffer 必须由 Host sizing 接口按 firstValue、diff、count 和 dtype 给出合法上下界，最小值是正确性门槛。
- [Arange](../../basic_api/reg_vector_compute/index_operations/arange.md)（`same_topic`）：高阶 LocalTensor Arange 提供同任务的 workspace 路径。
- [AscArange](../../c_api/reg/index_operate/asc_arange.md)（`same_topic`）：AscArange：AscArange、Reg Arange 与高级 Arange 都生成等差索引序列，差异在寄存器、LocalTensor和临时空间调用契约，适合实现路线互查。 目标卡《Arange（索引计算）》补充：给定起始值，等差值和长度，返回一个等差数列。
<!-- cannbot:related:end -->
