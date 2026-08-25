---
type: API
title: DataCopy（L0C Buffer到UB数据搬运）
description: 对数据搬运能力进行增强，相比于基础数据搬运接口，增加了L0C Buffer-\>Unified Buffer（UB）通路的随路计算。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/DataCopy_L0CToUB.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# DataCopy（L0C Buffer到UB数据搬运）

对 L0C Buffer→Unified Buffer（CO1→CO2）通路的数据搬运进行增强，增加随路反量化和 ReLU 计算。仅 Atlas 推理系列产品 AI Core 支持增强搬运功能，其他型号接口可调用但功能等同基础搬运。

参数：dst、src 为 LocalTensor；intriParams 为 DataCopyParams；enhancedParams 为 DataCopyEnhancedParams。关键字段：blockMode（BLOCK_MODE_MATRIX 为 16×16 分形 / BLOCK_MODE_VECTOR 为 1×16 分形）、deqScale（DEQ/DEQ8/DEQ16/VDEQ/VDEQ8/VDEQ16 量化模式）、deqValue（量化系数，含 M/N/MCB/Offset/Sign/ReLU 标志位）、deqTensorAddr（VDEQ 系列反量化参数向量地址，32 字节对齐）、sidStoreMode（DEQ8/VDEQ8 存储模式 0/1/2）、isRelu(bool)。

blockMode 与数据类型决定 blockLen/srcStride/dstStride 单位：MATRIX 模式 half/int16 为 512B、float/int32 为 1024B；VECTOR 模式 half/int16 为 32B、float/int32 为 64B。仅 Atlas 推理 AI Core 支持增强功能。
