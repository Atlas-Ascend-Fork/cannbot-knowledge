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

- [GetAxpyMaxMinTmpSize](get_axpy_max_min_tmp_size.md)（`related`）：源操作数(srcTensor)中每个元素与标量求积后和目的操作数(dstTensor)中的对应元素相加，计算公式如下： 该接口功能同基础API Axpy，区别在于此接口指令是通过Muls和Add组合计算，从而提供更优的精度。；kernel侧Axpy接口的计算需要开发者申请临时空间，本接口用于在host侧获取申请的最大和最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。；Axpy 定义 kernel 运算，Host helper 给出该运算的合法临时空间区间和 Tiling 传递方式，构成资源规划任务链。
- [GetAxpyTmpBufferFactorSize](get_axpy_tmp_buffer_factor_size.md)（`related`）：源操作数(srcTensor)中每个元素与标量求积后和目的操作数(dstTensor)中的对应元素相加，计算公式如下： 该接口功能同基础API Axpy，区别在于此接口指令是通过Muls和Add组合计算，从而提供更优的精度。；该接口用于获取maxLiveNodeCount和extraBuf，在固定空间大小的情况下，通过maxLiveNodeCount和extraBuf可以推算算子单次最大计算元素数量。；Axpy 的 Tiling 需要确定 calCount，factor helper 由固定 buffer 反推单次元素数，连接 Host 分块与 Device 调用规模。
<!-- cannbot:related:end -->
