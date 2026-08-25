---
type: API
title: GetAtanTmpBufferFactorSize
description: 获取Atan接口的maxLiveNodeCount和extraBuf，用于推算固定空间下单次最大计算元素数
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Atan_interface/GetAtanTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetAtanTmpBufferFactorSize

该接口用于获取maxLiveNodeCount和extraBuf，在固定空间大小的情况下，通过maxLiveNodeCount和extraBuf可以推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的多少倍；extraBuf表示使用的额外临时空间大小。 推算示例如下： - 算子实现需要调用Atan接口，开发者为其预留currBuff大小的空间，利用GetAtanTmpBufferFactorSize接口得到maxLiveNodeCount、extraBuf输出值，可推导算子单次最大计算元素数量为：

函数原型：void GetAtanTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- maxLiveNodeCount（输出）：最大存活节点数，表示临时空间是单次计算数据量所占空间的多少倍。
- extraBuf（输出）：使用的额外临时空间大小，单位为字节。

<!-- cannbot:related:start -->
## 相关

- [Atan](atan.md)（`related`）：factor 查询返回的 maxLiveNodeCount/extraBuf 用于按已分配临时空间推算 Atan 单次 calCount，直接决定 Kernel 侧 Atan 的分块规模。
- [Atan接口](atan_interface.md)（`same_topic`）：《Atan接口》处理“提供Atan反正切计算接口及其Tiling临时空间大小查询接口，包含Atan、GetAtanMaxMinTmpSize等。”。《GetAtanTmpBufferFactorSize》明确提供“获取Atan接口的maxLiveNodeCount和extraBuf，用于推算固定空间下单次最大计算元素数”，其参数、调用或验证步骤直接接入Atan Kernel 调用、临时空间查询和 SIMT 对应实现。
- [GetAtanMaxMinTmpSize](get_atan_max_min_tmp_size.md)（`same_topic`）：两者分别以形状上下界和线性因子描述同一个 Atan 临时空间需求，可结合可用 UB 选择 tiling 空间。
<!-- cannbot:related:end -->
