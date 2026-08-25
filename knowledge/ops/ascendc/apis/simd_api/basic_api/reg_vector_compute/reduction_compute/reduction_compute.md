---
type: API
title: 归约计算
description: Reg矢量计算归约接口索引页，包含Reduce、ReduceDataBlock与PairReduceElem。
tags: [task.lookup, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reduction_compute/reduction_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 归约计算

Reg矢量计算归约接口索引页，包含Reduce、ReduceDataBlock与PairReduceElem。

归约指令根据ReduceType，将数据集合简化为单一值或者更小的集合。 ReduceType::SUM：根据mask，计算源操作数srcReg内有效元素的数据总和，将结果写入目的操作数dstReg。 ReduceType::MAX：根据mask，计算源操作数srcReg内有效元素中的最大值和索引，将结果写入目的操作数dstReg，当存在多个最大值时，会将第一个最大值的索引保存在dstReg中。 ReduceType::MIN：根据mask，计算源操作数srcReg内有效元素中的最小值和索引，将结果写入目的操作数dstReg，当存在多个最小值时，会将第一个最小值的索引保存在dstReg中。

本接口组包含 Reduce, ReduceDataBlock, PairReduceElem。

本接口属于 Reg 矢量计算归约接口，对 RegTensor 数据进行归约运算。

约束：对于归约求数据总和，mask指定源操作数是否参与计算，不参与计算的元素，被当作0进行处理。；对于归约求最大值，mask指定源操作数是否参与计算，不参与计算的元素，被当作数据类型的最小值进行处理。；对于归约求最小值，mask指定源操作数是否参与计算，不参与计算的元素，被当作数据类型的最大值进行处理。；对于归约求最大值，当所有元素均不参与计算时，将该数据类型的最小值写入dstReg，当存在多个最大值时，会将第一个最大值的索引保存在dstReg中，max(-0, +0) = +0。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [ACL 507035 — 完整 a0 统计缓冲超过 UB](../../../../../runbooks/compilation/ub_slices_reduction_axis_scratch_buffers_507035.md)（`exemplifies`）：《归约计算》处理“Reg矢量计算归约接口索引页，包含Reduce、ReduceDataBlock与PairReduceElem。”。《ACL 507035 — 完整 a0 统计缓冲超过 UB》提供“ARA 按完整尾轴乘积分配 fp32 max/sum 缓冲会在大 a0 时超过 UB；须对 a0 再切 tile 并逐 tile 完成三趟归约。”，其具体合同或探针直接接入规约 count、尾部填充、并行切核和 UB 容量的直接正确性约束。
- [DataCopyPad 未填满强制对齐缓冲 — 小维规约读入脏尾部](../../../../../runbooks/precision/datacopypad_tail_must_initialize_full_reduction_extent.md)（`exemplifies`）：《归约计算》处理“Reg矢量计算归约接口索引页，包含Reduce、ReduceDataBlock与PairReduceElem。”。《DataCopyPad 未填满强制对齐缓冲 — 小维规约读入脏尾部》提供“行缓冲强制扩到固定向量长度、rightPadding 却只覆盖较短 DMA 边界时，小归一化维会把未初始化 UB 尾部纳入规约；用 32/sizeof(T) 统一分配与补零粒度。”，其具体合同或探针直接接入规约 count、尾部填充、并行切核和 UB 容量的直接正确性约束。
- [每核最少行数地板压低 AIV 并行度—按可用核数切分](../../../../../runbooks/performance/row_reduction_min_rows_floor_underutilizes_aiv.md)（`exemplifies`）：《归约计算》处理“Reg矢量计算归约接口索引页，包含Reduce、ReduceDataBlock与PairReduceElem。”。《每核最少行数地板压低 AIV 并行度—按可用核数切分》提供“行级归约 tiling 不应先用每核最少行数限制 block 数；按可用 AIV 核数上限切分可恢复并行度。”，其具体合同或探针直接接入规约 count、尾部填充、并行切核和 UB 容量的直接正确性约束。
- [如何使用归约计算API](../../../../../guides/programming_guide/library_api/basic_api/quick_reference/how_to_use_reduction_api.md)（`explains`）：如何使用归约计算API 与《归约计算》的实质衔接是：该指南解释 ReduceMax/Min/Sum、Repeat、DataBlock、PairElem 的粒度以及 mask/repeat 参数；基础/Reg 总览、辅助配置和 padding/count 故障直接影响选型与结果正确性。
- [ReduceMin](../../memory_vector_compute/reduction_compute/reduce_min.md)（`same_topic`）：ReduceMin 与《归约计算》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
- [归约操作](../../../adv_api/reduction_operations/reduction_operations.md)（`same_topic`）：归约操作 与《归约计算》的实质衔接是：归约导航本身由 part_of 覆盖接口成员；这里只连接跨层归约概述/使用指南及 padding、UB、累加和多行执行等直接影响选择与验收的故障卡。
- [归约计算概述](../../memory_vector_compute/reduction_compute/introduction.md)（`same_topic`）：归约计算概述 与《归约计算》的实质衔接是：基础归约概述说明 pair、datablock、repeat 与全量 reduce 的粒度选择；使用指南和故障卡限定有效 count、对齐尾部、work buffer、累加类型及多行验证。
<!-- cannbot:related:end -->
