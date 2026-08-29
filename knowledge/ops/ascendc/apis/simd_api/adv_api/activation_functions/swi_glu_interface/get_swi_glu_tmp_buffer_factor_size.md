---
type: API
title: GetSwiGLUTmpBufferFactorSize
description: 获取SwiGLU接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SwiGLU_interface/GetSwiGLUTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetSwiGLUTmpBufferFactorSize

kernel侧SwiGLU接口的计算需要开发者预留 申请临时空间，最大临时空间（maxTmpBuffer）和输入所占空间（inputSize * typeSize）存在以下关系： maxTmpBuffer = maxLiveNodeCount * inputSize * typeSize + extraBuffer 其中maxLiveNodeCount表示最大临时空间是输入所占空间的多少倍；extraBuffer表示使用的额外临时空间大小。

函数原型：void GetSwiGLUTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuffer)

参数：
- 接口（输入 输出）：功能
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- maxLiveNodeCount（输出）：最大存活节点数，最大临时空间是输入所占空间的多少倍。
- extraBuffer（输出）：使用的额外临时空间大小，单位为byte。

<!-- cannbot:related:start -->
## 相关

- [GetSwiGLUMaxMinTmpSize](get_swi_glu_max_min_tmp_size.md)（`related`）：“- maxValue（输出）：SwiGLU接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。”；“- maxLiveNodeCount（输出）：最大存活节点数，最大临时空间是输入所占空间的多少倍。”。两种 Host 查询分别给定绝对空间范围和按输入规模反推空间的因子，服务同一 SwiGLU tiling 预算。
- [SwiGLU](swi_glu.md)（`related`）：“__aicore__ inline void SwiGLU(LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor0, const LocalTensor<T>& srcTensor1, const float& scalarValue, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t calCount)”与“kernel侧SwiGLU接口的计算需要开发者预留 申请临时空间，最大临时空间（maxTmpBuffer）和输入所占空间（inputSize * typeSize）存在以下关系： maxTmpBuffer = maxLiveNodeCount * inputSize * typeSize + extraBuffer 其中maxLiveNodeCount表示最大临时空间是输入所占空间的多少倍；extraBuffer表示使用的额外临时空间大小。”提供双方正文证据。SwiGLU 原型要求 sharedTmpBuffer，helper 给出 maxLiveNodeCount 与 extraBuffer 计算该缓冲区容量，构成实际调用前的空间准备。
<!-- cannbot:related:end -->
