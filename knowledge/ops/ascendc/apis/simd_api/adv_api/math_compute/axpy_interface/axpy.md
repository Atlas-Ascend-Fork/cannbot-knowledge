---
type: API
title: Axpy
description: 源操作数各元素与标量求积后加到目的操作数对应元素，通过Muls和Add组合提升精度
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Axpy_interface/Axpy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Axpy

源操作数(srcTensor)中每个元素与标量求积后和目的操作数(dstTensor)中的对应元素相加，计算公式如下： 该接口功能同基础API Axpy，区别在于此接口指令是通过Muls和Add组合计算，从而提供更优的精度。

函数原型：
template <typename T, typename U, bool isReuseSource = false>
__aicore__ inline void Axpy(const LocalTensor<T>& dstTensor, const LocalTensor<U>& srcTensor, const U scalarValue, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t calCount)

参数：
- T：目的操作数的数据类型。支持的数据类型为：half、float。
- U：源操作数的数据类型。支持的数据类型为：half、float。
- isReuseSource：是否允许修改源操作数。该参数预留，传入默认值false即可。
- dstTensor（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- srcTensor（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。

约束：
- 不支持源操作数与目的操作数地址重叠。
- 不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。
- 操作数地址对齐要求请参见通用地址对齐约束。
- 该接口支持的精度组合如下：
- half精度组合：srcLocal数据类型=half；scalar数据类型=half；dstLocal数据类型=half；PAR=128

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [AscAxpy](../../../c_api/vector_compute/asc_axpy.md)（`related`）：高阶 Axpy 用 Muls+Add 组合并配套临时空间，适合需要高阶 tiling/精度实现的场景。
- [Axpy](../../../basic_api/memory_vector_compute/composite_compute/axpy.md)（`related`）：Axpy 与《Axpy》的实质衔接是：Axpy 把缩放源加到目的，需与高阶 Axpy、mask/repeat 和临时空间查询配套。
- [GetAxpyTmpBufferFactorSize](get_axpy_tmp_buffer_factor_size.md)（`related`）：该因子接口可从固定临时空间反推 Axpy 单次最大处理元素数，用于决定 calCount 分块。
- [AscAxpy](../../../c_api/reg/compound_compute/asc_axpy.md)（`same_topic`）：AscAxpy 与《Axpy》的衔接是：AscAxpy 的 C Vector、基础及高阶 Axpy 入口实现同一 alpha*x+y 数据流，差异集中在张量形态、临时空间和调度层级。
- [Axpy接口](axpy_interface.md)（`same_topic`）：该接口页定义的临时空间、地址不重叠和 y=a*x+y 契约由 Axpy 计算接口直接实现。
- [GetAxpyMaxMinTmpSize](get_axpy_max_min_tmp_size.md)（`same_topic`）：GetAxpyMaxMinTmpSize 与《Axpy》的实质衔接是：Axpy 的 max-min/factor 查询直接服务 Axpy kernel 与 SIMD/C API 实现。
<!-- cannbot:related:end -->
