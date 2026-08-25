---
type: API
title: Gatherb
description: 根据DataBlock偏移张量将输入张量按DataBlock粒度收集到结果张量中，每次迭代完成8个DataBlock的数据收集。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/scatter_gather/Gatherb_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Gatherb

根据DataBlock偏移张量将输入张量按DataBlock粒度收集到结果张量中，每次迭代完成8个DataBlock的数据收集。

本接口组包含 LocalTensor, Reg矢量计算。

本接口属于 UB 矢量计算 Scatter/Gather 接口。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AscGather](../../../c_api/vector_compute/asc_gather.md)（`related`）：AscGather 与《Gatherb》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [Gather](gather.md)（`related`）：《Gatherb》明确“根据DataBlock偏移张量将输入张量按DataBlock粒度收集到结果张量中，每次迭代完成8个DataBlock的数据收集。”；它与《Gather》的“根据基地址和地址偏移张量确定索引，将输入张量中对应元素收集到结果张量中，支持前n个数据和高维切分计算。”在实际调用参数、数据流或结果校验上直接衔接。
- [GatherB](../../reg_vector_compute/reg_data_load/gather_b_discrete.md)（`same_topic`）：Gatherb 与 Reg GatherB 都按 DataBlock 偏移从 UB 收集数据；一张描述 Memory 接口组，一张给出寄存器离散加载入口。
<!-- cannbot:related:end -->
