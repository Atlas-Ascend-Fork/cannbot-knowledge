---
type: API
title: BitwiseXor
description: 逐比特对两个输入进行异或操作。 !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/BitwiseXor_interface/BitwiseXor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# BitwiseXor

逐比特对两个输入进行异或操作。

函数原型：
template <const BitwiseXorConfig& config = DEFAULT_BITWISE_XOR_CONFIG, typename T>
__aicore__ inline void BitwiseXor(const LocalTensor<T>& dst, const LocalTensor<T>& src0, const LocalTensor<T>& src1, const uint32_t count)

参数：
- config：BitwiseXor算法的相关配置。此参数可选配，BitwiseXorConfig类型，具体定义如下方代码所示，其中参数的含义为： isReuseSource：该参数预留，传入默认值false即可。
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

- [GetBitwiseXorMaxMinTmpSize](get_bitwise_xor_max_min_tmp_size.md)（`related`）：Kernel侧BitwiseXor接口的计算需要开发者预留 申请临时空间，本接口用于在Host侧获取预留 申请的最大和最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到Kernel侧使用。；函数原型： template <const BitwiseXorConfig& config = DEFAULT_BITWISE_XOR_CONFIG, typename T> __aicore__ inline void BitwiseXor(const LocalTensor<T>& dst, const LocalTensor<T>& src0, const LocalTensor<T>& src1, const uint32_t count)；Host 查询接口专门为该 BitwiseXor Kernel 计算确定临时空间上下界，计算接口是这份 Tiling 参数的消费对象。
- [GetBitwiseXorTmpBufferFactorSize](get_bitwise_xor_tmp_buffer_factor_size.md)（`related`）：该接口用于获取maxLivedNodeCount和extraBuf，在固定空间大小的情况下，通过maxLivedNodeCount和extraBuf可以推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的多少倍；extraBuf表示使用的额外临时空间大小。 推算示例如下： - 算子实现需要调用BitwiseXor接口，开发者为其预留currBuff大小的空间，利用GetBitwiseXorTmpBufferFactorSize接口得到maxLivedNodeCount、extraBuf输出值，可推导算子单次最大计算元素数量为：；逐比特对两个输入进行异或操作。；因算子实现实际调用 BitwiseXor，factor 查询返回的 maxLivedNodeCount 与 extraBuf 正是规划该计算每次处理量和临时空间的 Host 侧依据。
<!-- cannbot:related:end -->
