---
type: API
title: Gather
description: 根据基地址和地址偏移张量确定索引，将输入张量中对应元素收集到结果张量中，支持前n个数据和高维切分计算。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/scatter_gather/Gather.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Gather

按索引收集接口，根据索引 tensor 从源 tensor 中收集元素到目的 tensor。头文件 `basic_api/kernel_operator_vec_intf.h`。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Gather 双加 LocalTensor 基址导致交错旋转乱码](../../../../../runbooks/precision/localtensor_gather_base_address_not_double_counted.md)（`exemplifies`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《Gather》明确提供“根据基地址和地址偏移张量确定索引，将输入张量中对应元素收集到结果张量中，支持前n个数据和高维切分计算。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [AscGather](../../../c_api/vector_compute/asc_gather.md)（`related`）：AscGather 与《Gather》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [CreateVecIndex](../data_padding/create_vec_index.md)（`related`）：CreateVecIndex 生成从 firstValue 递增的索引 Tensor，可直接作为 Gather 的索引输入。
- [Gatherb](gatherb_isasi.md)（`related`）：《Gatherb》明确“根据DataBlock偏移张量将输入张量按DataBlock粒度收集到结果张量中，每次迭代完成8个DataBlock的数据收集。”；它与《Gather》的“根据基地址和地址偏移张量确定索引，将输入张量中对应元素收集到结果张量中，支持前n个数据和高维切分计算。”在实际调用参数、数据流或结果校验上直接衔接。
- [Gather](../../reg_vector_compute/scatter_operations/gather.md)（`same_topic`）：《Gather》明确“根据索引值将源操作数按元素收集到目的操作数中，支持b8、b16、b32数据类型。”；它与《Gather》的“根据基地址和地址偏移张量确定索引，将输入张量中对应元素收集到结果张量中，支持前n个数据和高维切分计算。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
