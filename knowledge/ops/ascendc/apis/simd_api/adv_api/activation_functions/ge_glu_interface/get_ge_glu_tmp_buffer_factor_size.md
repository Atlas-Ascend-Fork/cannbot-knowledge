---
type: API
title: GetGeGLUTmpBufferFactorSize
description: 获取GeGLU接口的maxLiveNodeCount和extraBuf，用于推算固定空间下单次最大计算元素数
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/GeGLU_interface/GetGeGLUTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetGeGLUTmpBufferFactorSize

kernel侧GeGLU接口的计算需要开发者预留 申请临时空间，最大临时空间（maxTmpBuffer）和输入所占空间（inputSize * typeSize）存在以下关系： maxTmpBuffer = maxLiveNodeCount * inputSize * typeSize + extraBuf 其中maxLiveNodeCount表示最大临时空间是输入所占空间的多少倍；extraBuf表示使用的额外临时空间大小。

函数原型：void GetGeGLUTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：
- 接口（输入 输出）：功能
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- maxLiveNodeCount（输出）：最大存活节点数，最大临时空间是输入所占空间的多少倍。
- extraBuf（输出）：使用的额外临时空间大小，单位为字节。

<!-- cannbot:related:start -->
## 相关

- [GeGLU](ge_glu.md)（`same_topic`）：GetGeGLUTmpBufferFactorSize 与《GeGLU》的实质衔接是：该 factor 查询把 GeGLU 的 maxLiveNodeCount/extraBuf 与最大最小临时空间合并，直接推导 GeGLU 固定 UB 下的单次处理量。
- [GeGLU接口](ge_glu_interface.md)（`same_topic`）：GetGeGLUTmpBufferFactorSize 与《GeGLU接口》的实质衔接是：该 factor 查询把 GeGLU 的 maxLiveNodeCount/extraBuf 与最大最小临时空间合并，直接推导 GeGLU 固定 UB 下的单次处理量。
- [GetGeGLUMaxMinTmpSize](get_ge_glu_max_min_tmp_size.md)（`same_topic`）：GetGeGLUTmpBufferFactorSize 与《GetGeGLUMaxMinTmpSize》的实质衔接是：该 factor 查询把 GeGLU 的 maxLiveNodeCount/extraBuf 与最大最小临时空间合并，直接推导 GeGLU 固定 UB 下的单次处理量。
<!-- cannbot:related:end -->
