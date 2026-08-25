---
type: API
title: BitwiseOr
description: 逐比特对两个输入进行或操作。 !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/BitwiseOr_interface/BitwiseOr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# BitwiseOr

逐比特对两个输入进行或操作。

函数原型：
template <const BitwiseOrConfig& config = DEFAULT_BITWISE_OR_CONFIG, typename T>
__aicore__ inline void BitwiseOr(const LocalTensor<T>& dst, const LocalTensor<T>& src0, const LocalTensor<T>& src1, const uint32_t count)

参数：
- config：BitwiseOr算法的相关配置。此参数可选配，BitwiseOrConfig类型，具体定义如下方代码所示，其中参数的含义为： isReuseSource：该参数预留，传入默认值false即可。
- T：源操作数、目的操作数数据类型。支持的数据类型为：int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、int64_t、uint64_t。
- dst（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- src0、src1（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 数据类型需要与目的操作数保持一致。
- count（输入）：参与计算的元素个数。

约束：
- 不支持源操作数与目的操作数地址重叠。
- 操作数地址偏移对齐要求请参见通用说明和约束。

支持：Ascend 950PR/Ascend 950DT。不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetBitwiseOrMaxMinTmpSize](get_bitwise_or_max_min_tmp_size.md)（`same_topic`）：GetBitwiseOrMaxMinTmpSize 与《BitwiseOr》的实质衔接是：该查询只给出 BitwiseOr/MaxMin 类算子的 sharedTmpBuffer 大小，factor 参数与实际 BitwiseOr kernel 调用是分配空间所必需的两端。
- [GetBitwiseOrTmpBufferFactorSize](get_bitwise_or_tmp_buffer_factor_size.md)（`same_topic`）：GetBitwiseOrTmpBufferFactorSize 与《BitwiseOr》的实质衔接是：factor 查询与 GetBitwiseOrMaxMinTmpSize、BitwiseOr Kernel 是同一 sharedTmpBuffer 契约的固定空间反推、空间边界和实际消费三端。
<!-- cannbot:related:end -->
