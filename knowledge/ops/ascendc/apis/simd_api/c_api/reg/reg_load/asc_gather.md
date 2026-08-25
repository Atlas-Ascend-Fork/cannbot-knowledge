---
type: API
title: AscGather
description: 根据索引位置index将源操作数src按元素收集到目的操作数dst中。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_gather.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# AscGather

根据索引位置index将源操作数src按元素收集到目的操作数dst中。 图 1  收集UB中的元素 图 2  收集矢量数据寄存器中的元素
函数原型：void asc_gather(vector_int16_t& dst, __ubuf__ int8_t* src, vector_uint16_t index, vector_bool mask)
约束：收集UB中的元素；源操作数在UB中的起始地址需要32B对齐。；对于mask筛选需要搬运的元素，对应的地址需要在UB有效范围内；对于mask未筛选的元素，对应的地址不会触发任何地址越界异常，同时dst中对应的元素将被置零。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Gather 双加 LocalTensor 基址导致交错旋转乱码](../../../../../runbooks/precision/localtensor_gather_base_address_not_double_counted.md)（`exemplifies`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《AscGather》明确提供“根据索引位置index将源操作数src按元素收集到目的操作数dst中。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [AscGather](../../vector_compute/asc_gather.md)（`related`）：AscGather 与《AscGather》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [AscGatherDatablock](asc_gather_datablock.md)（`same_topic`）：《AscGather》明确“根据索引位置index将源操作数src按元素收集到目的操作数dst中。”；它与《AscGatherDatablock》的“根据索引将UB中的源操作数按32B的DataBlock收集到目的操作数中。”在实际调用参数、数据流或结果校验上直接衔接。
- [Gather](../../../basic_api/reg_vector_compute/reg_data_load/gather_discrete.md)（`same_topic`）：两者都从 UB 基址按逐元素 index 收集到寄存器；基础 Reg Gather 明确 index 单位为元素及类型组合，补足 C AscGather 的参数语义。
- [Gather](../../../basic_api/reg_vector_compute/scatter_operations/gather.md)（`same_topic`）：《Gather》说明根据索引值将源操作数按元素收集到目的操作数中，支持b8、b16、b32数据类型。；《AscGather》说明根据索引位置index将源操作数src按元素收集到目的操作数dst中。。二者在Reg Gather的index和baseAddr寻址合同与C API等价接口、维序/步长及LocalTensor基址故障直接对应上存在可执行的直接衔接。
<!-- cannbot:related:end -->
