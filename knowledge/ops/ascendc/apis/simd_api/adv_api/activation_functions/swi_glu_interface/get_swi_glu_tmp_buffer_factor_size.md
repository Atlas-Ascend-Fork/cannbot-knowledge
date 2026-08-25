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

- [GetSwiGLUMaxMinTmpSize](get_swi_glu_max_min_tmp_size.md)（`same_topic`）：两者是 SwiGLU Host 侧临时空间预算的互补查询：本接口给出合法上下界，FactorSize 接口用 live-node/factor 模型估算可处理规模。
- [SwiGLU](swi_glu.md)（`same_topic`）：SwiGLU 与《GetSwiGLUTmpBufferFactorSize》的实质衔接是：SwiGLU 的 kernel、两种临时空间查询与非 32B slice 精度故障共同约束调用和缓冲区分配。
<!-- cannbot:related:end -->
