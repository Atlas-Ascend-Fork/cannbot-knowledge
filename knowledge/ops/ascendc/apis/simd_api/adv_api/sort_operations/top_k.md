---
type: API
title: TopK
description: 获取最后一个维度的前k个最大值或最小值及其对应的索引，最多支持二维输入。整数倍，所以当n不是32的
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/TopK.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TopK

获取最后一个维度的前k个最大值或最小值及其对应的索引。输入为向量时对全部元素操作，输入为矩阵时沿最后一维对每行操作。最多支持二维输入。支持Normal模式（通用）和Small模式（内轴长度固定为32时的高性能模式）。模板参数T支持half/float。

提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。Tiling参数通过TopK Tiling获取。接口参数：dstValue输出前k个值；dstIndex输出对应索引；srcTensor输入数据（内轴长度需32对齐，不满足时需补齐）；sharedTmpBuffer临时缓存；topKParams含outter、inner、k等信息。

约束：最多支持二维输入；内轴长度需32B对齐；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [TopK BF16 tie 索引顺序与 CPU 不一致](../../../../runbooks/precision/topk_bf16_tie_cpu.md)（`exemplifies`）：本算子在 plugin 层把 BF16 先 Cast 为 float32 再调 `AscendC::TopK<float>`、结果 Cast 回 BF16。；获取最后一个维度的前k个最大值或最小值及其对应的索引。输入为向量时对全部元素操作，输入为矩阵时沿最后一维对每行操作。；故障卡直接调用目标 TopK API，并围绕其 values/indices 输出诊断 BF16 tie 的索引差异。
- [TopKTiling](top_k_tiling.md)（`related`）：提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。Tiling参数通过TopK Tiling获取。；host侧Tiling接口，用于获取TopK kernel计算所需的Tiling参数，分两步：通过GetTopKMaxMinTmpSize获取最大和最小临时空间大小；通过GetTopKNDTilingInfo获取kernel侧所需tiling参数。计算接口明确依赖后者生成临时空间与 TopKParams，形成 Host Tiling 到 Kernel 调用的直接契约。
<!-- cannbot:related:end -->
