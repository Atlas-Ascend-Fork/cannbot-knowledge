---
type: API
title: BitwiseAnd
description: 逐比特对两个输入进行与操作。 !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/BitwiseAnd_interface/BitwiseAnd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# BitwiseAnd

逐比特对两个输入进行与操作。

函数原型：
template <const BitwiseAndConfig& config = DEFAULT_BITWISE_AND_CONFIG, typename T>
__aicore__ inline void BitwiseAnd(const LocalTensor<T>& dst, const LocalTensor<T>& src0, const LocalTensor<T>& src1, const uint32_t count)

参数：
- config：BitwiseAnd算法的相关配置。此参数可选配，BitwiseAndConfig类型，具体定义如下方代码所示，其中参数的含义为： isReuseSource：该参数预留，传入默认值false即可。
- T：操作数的数据类型。支持的数据类型为：int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、int64_t、uint64_t。
- dst（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- src0、src1（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 源操作数的数据类型与目的操作数保持一致。
- count（输入）：参与计算的元素个数。

约束：
- 不支持源操作数与目的操作数地址重叠。
- 操作数地址对齐要求请参见通用地址对齐约束。

支持：Ascend 950PR/Ascend 950DT。不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetBitwiseAndMaxMinTmpSize](get_bitwise_and_max_min_tmp_size.md)（`related`）：__aicore__ inline void BitwiseAnd(const LocalTensor<T>& dst, const LocalTensor<T>& src0, const LocalTensor<T>& src1, const uint32_t count)；Kernel侧BitwiseAnd接口的计算需要开发者预留 申请临时空间，本接口用于在Host侧获取预留 申请的最大和最小临时空间大小；Kernel API 以 count 定义本次工作量，Host 查询为其底层实现提供合法临时空间范围，调用方据此同时确定分块元素数与 Tiling buffer 容量。
- [GetBitwiseAndTmpBufferFactorSize](get_bitwise_and_tmp_buffer_factor_size.md)（`related`）：- count（输入）：参与计算的元素个数。；该接口用于获取maxLivedNodeCount和extraBuf，在固定空间大小的情况下，通过maxLivedNodeCount和extraBuf可以推算算子单次最大计算元素数量。；factor 查询把固定临时空间换算成 BitwiseAnd 单次最大元素数，该结果直接作为 Kernel count 的分块上限。
<!-- cannbot:related:end -->
