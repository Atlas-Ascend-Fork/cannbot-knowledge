---
type: API
title: AscGather
description: 将src按照src_offset给定的偏移按元素收集到dst中。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_gather.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscGather

将src按照src_offset给定的偏移按元素收集到dst中。
函数原型：void asc_gather(__ubuf__ int16_t* dst, __ubuf__ int16_t* src, __ubuf__ uint32_t* src_offset, uint32_t count)
约束：src_offset里的偏移量取值应保证src元素类型位宽对齐。；src加上src_offset偏移后的地址不能超出Unified Buffer (UB)大小数据的范围。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [Gather 双加 LocalTensor 基址导致交错旋转乱码](../../../../runbooks/precision/localtensor_gather_base_address_not_double_counted.md)（`exemplifies`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《AscGather》明确提供“将src按照src_offset给定的偏移按元素收集到dst中。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [Gather 非 dim 维缩小时折叠步长错位](../../../../runbooks/precision/gather_non_axis_shape_shrink_requires_per_axis_source_strides.md)（`exemplifies`）：AscGather 与《Gather 非 dim 维缩小时折叠步长错位》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [Gather 非 last-dim 转置+索引换算预处理占比高](../../../../runbooks/performance/gather_last_dim.md)（`exemplifies`）：AscGather 与《Gather 非 last-dim 转置+索引换算预处理占比高》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [LocalTensor SetValue 参数颠倒导致索引错乱](../../../../runbooks/precision/localtensor_setvalue_uses_offset_then_value.md)（`exemplifies`）：AscGather 与《LocalTensor SetValue 参数颠倒导致索引错乱》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [gather 扁平偏移公式 dim 上方形状错配](../../../../runbooks/precision/gather_dim.md)（`exemplifies`）：AscGather 与《gather 扁平偏移公式 dim 上方形状错配》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [多维 Gather 部分 case 错 — LUT 维序反了](../../../../runbooks/precision/gather_lut_coordinate_decode_must_start_from_last_dimension.md)（`exemplifies`）：AscGather 与《多维 Gather 部分 case 错 — LUT 维序反了》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [逐元素 DataCopyPad 做 strided gather 输出全零](../../../../runbooks/precision/datacopypad_strided_gather.md)（`exemplifies`）：AscGather 与《逐元素 DataCopyPad 做 strided gather 输出全零》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [随机 Gather 每元素 DMA 过慢—改 SIMT 直访 GM](../../../../runbooks/performance/random_gather_per_element_dma_should_switch_to_simt_direct_gm.md)（`exemplifies`）：AscGather 与《随机 Gather 每元素 DMA 过慢—改 SIMT 直访 GM》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [Gather算子快速入门](../../../../guides/getting_started/quick_start/simt_programming/gather_op_quick_start.md)（`explains`）：AscGather 与《Gather算子快速入门》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [AscGather](../reg/reg_load/asc_gather.md)（`related`）：AscGather 与《AscGather》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [AscGatherDatablock](asc_gather_datablock.md)（`related`）：AscGather 按元素偏移收集，AscGatherDatablock 按 32B 块收集；数据离散粒度决定应选哪一个接口。
- [Gather](../../basic_api/memory_vector_compute/scatter_gather/gather.md)（`related`）：AscGather 与《Gather》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [Gather](../../basic_api/reg_vector_compute/reg_data_load/gather_discrete.md)（`related`）：AscGather 与《Gather》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [Gather](../../basic_api/reg_vector_compute/scatter_operations/gather.md)（`related`）：《Gather》说明根据索引值将源操作数按元素收集到目的操作数中，支持b8、b16、b32数据类型。；《AscGather》说明将src按照src_offset给定的偏移按元素收集到dst中。。二者在Reg Gather的index和baseAddr寻址合同与C API等价接口、维序/步长及LocalTensor基址故障直接对应上存在可执行的直接衔接。
- [GatherB](../../basic_api/reg_vector_compute/reg_data_load/gather_b_discrete.md)（`related`）：AscGather 与《GatherB》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [Gatherb](../../basic_api/memory_vector_compute/scatter_gather/gatherb_isasi.md)（`related`）：AscGather 与《Gatherb》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [Reg数据搬入](../../basic_api/reg_vector_compute/reg_data_load/reg_data_load.md)（`related`）：AscGather 与《Reg数据搬入》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [Reg矢量计算离散操作](../../basic_api/reg_vector_compute/scatter_operations/scatter_operations.md)（`related`）：AscGather 与《Reg矢量计算离散操作》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [reg数据搬入](../reg/reg_load/reg_load.md)（`related`）：AscGather 与《reg数据搬入》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
<!-- cannbot:related:end -->
