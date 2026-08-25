---
type: API
title: GetCeilTmpBufferFactorSize
description: 获取Ceil接口的maxLiveNodeCount和extraBuf，用于推算固定空间下单次最大计算元素数
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Ceil_interface/GetCeilTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetCeilTmpBufferFactorSize

该接口用于获取maxLiveNodeCount和extraBuf，在固定空间大小的情况下，通过maxLiveNodeCount和extraBuf可以推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的多少倍；extraBuf表示使用的额外临时空间大小。 推算示例如下： - 算子实现需要调用Ceil接口，开发者为其预留currBuff大小的空间，利用GetCeilTmpBufferFactorSize接口得到maxLiveNodeCount、extraBuf输出值，可推导算子单次最大计算元素数量为：

函数原型：void GetCeilTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- maxLiveNodeCount（输出）：最大存活节点数，表示临时空间是单次计算数据量所占空间的多少倍。
- extraBuf（输出）：使用的额外临时空间大小，单位为字节。

<!-- cannbot:related:start -->
## 相关

- [tmpBuffer 分配步长≠访问步长触发 UB 越界 341](../../../../../runbooks/compilation/tmpbuffer_ub_341.md)（`exemplifies`）：GetCeilTmpBufferFactorSize 与《tmpBuffer 分配步长≠访问步长触发 UB 越界 341》的实质衔接是：factor 查询与 GetCeilMaxMinTmpSize 共同换算 Ceil 单次元素数，Ceil/C API 是消费端；tmpBuffer 步长故障直接验证空间公式错误会造成 UB 越界。
- [AscCeil](../../../c_api/reg/data_type_convert/asc_ceil.md)（`related`）：GetCeilTmpBufferFactorSize 与《AscCeil》的实质衔接是：factor 查询与 GetCeilMaxMinTmpSize 共同换算 Ceil 单次元素数，Ceil/C API 是消费端；tmpBuffer 步长故障直接验证空间公式错误会造成 UB 越界。
- [Ceil](ceil.md)（`same_topic`）：GetCeilTmpBufferFactorSize 与《Ceil》的实质衔接是：factor 查询与 GetCeilMaxMinTmpSize 共同换算 Ceil 单次元素数，Ceil/C API 是消费端；tmpBuffer 步长故障直接验证空间公式错误会造成 UB 越界。
- [Ceil接口](ceil_interface.md)（`same_topic`）：《Ceil接口》说明提供Ceil向上取整计算接口及其Tiling临时空间大小查询接口，包含Ceil、GetCeilMaxMinTmpSize等。；《GetCeilTmpBufferFactorSize》说明获取Ceil接口的maxLiveNodeCount和extraBuf，用于推算固定空间下单次最大计算元素数。二者在Ceil计算、临时空间估算与多核尾段切分共同决定向上取整算子的正确执行上存在可执行的直接衔接。
- [GetCeilMaxMinTmpSize](get_ceil_max_min_tmp_size.md)（`same_topic`）：MaxMin 接口给出 Ceil workspace 合法区间，factor 接口再由实际空间反算单次处理量，是同一 tiling 公式的正反两侧。
<!-- cannbot:related:end -->
