---
type: API
title: Ceil
description: 获取大于或等于输入值的最小整数，即向正无穷方向取整
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Ceil_interface/Ceil.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# Ceil

获取大于或等于x的最小的整数值，即向正无穷取整操作。计算公式如下： 举例如下： Ceil(3.9) = 4.0

函数原型：
template <typename T, bool isReuseSource = false>
__aicore__ inline void Ceil(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t calCount)

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isReuseSource：是否允许修改源操作数。该参数预留，传入默认值false即可。
- dstTensor（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- srcTensor（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 源操作数的数据类型需要与目的操作数保持一致。
- sharedTmpBuffer（输入）：临时缓存。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 用于Ceil内部复杂计算时存储中间变量，由开发者提供。 临时空间大小BufferSize的获取方式请参考GetCeilMaxMinTmpSize。

约束：
- 针对Atlas 推理系列产品AI Core，输入数据限制在[-2147483647.0, 2147483647.0]范围内。
- 不支持源操作数与目的操作数地址重叠。
- 不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。
- 操作数地址对齐要求请参见通用地址对齐约束。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetCeilMaxMinTmpSize](get_ceil_max_min_tmp_size.md)（`related`）：Ceil 接口直接声明“临时空间大小BufferSize的获取方式请参考GetCeilMaxMinTmpSize。”；Host 接口说明“kernel侧Ceil接口的计算需要开发者预留 申请临时空间，本接口用于在host侧获取预留 申请的最大和最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。”，两端构成 Ceil sharedTmpBuffer 的 Host 容量生产与 Kernel 消费链，但分别承担容量规划和数值计算两个主题。
- [GetCeilTmpBufferFactorSize](get_ceil_tmp_buffer_factor_size.md)（`related`）：“该接口用于获取maxLiveNodeCount和extraBuf，在固定空间大小的情况下，通过maxLiveNodeCount和extraBuf可以推算算子单次最大计算元素数量。”给出 Ceil 临时区容量推导；“用于Ceil内部复杂计算时存储中间变量，由开发者提供。”确认 Ceil 实际消费该临时缓存，因此能直接用于实现时的 tile 上限计算。
<!-- cannbot:related:end -->
