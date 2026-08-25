---
type: API
title: DataCopy
description: 支持GM与UB之间的连续数据搬运，数据传输过程中保持原始格式和内容不变。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_GMAndUB_continuous.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# DataCopy

支持GM与UB之间的连续数据搬运，数据传输过程中保持原始格式和内容不变。

如下图1所示，完成同一流水线内的同步控制，用于在同一流水线内部约束执行顺序。其作用是，保证前序指令中所有数据的读写工作全部完成，后序指令才能执行。 图1 PipeBarrier接口功能示意图

本接口组包含 逻辑位置TPosition, PipeBarrier(ISASI)。

本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

约束：Scalar流水之间的同步由硬件自动保证，PipeBarrier接口不支持PIPE_S单流水的同步。；PipeBarrier ()会等待所有流水线中所有先前提交的接口完成，这会对性能产生影响。若仅阻塞单条流水线即可解决问题，应避免随意调用PipeBarrier ()。；PIPE_MTE2/PIPE_MTE3在搬运地址有重叠的情况下需要开发者插入同步。例如，当需要执行多个DataCopy指令，且DataCopy的目的地址存在重叠时，需要通过调用来插入PipeBarrier同步指令，保证多个DataCopy指令的串行化，防止出现异常数据。如下图左侧示意图，执行两个DataCopy指令，搬运的目的GM地址存在重叠，两条搬运指令之间需要通过调用PipeBarrier ()添加MTE3搬出流水的同步；如下图右侧示意图所示，搬运的目的地址UB存在重叠，两条搬运指令之间需要调用PipeBarrier ()添加MTE2搬入流水的同步。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 DataCopy 写回 L2 驱逐丢对角线](../../../../../runbooks/precision/ascend950_datacopy_l2.md)（`exemplifies`）：DataCopy 是 dense path 批量 UB→GM 写回的直接执行接口；多核写入量超过 L2 时应避免整 tile 回写并改为只写修改元素。
- [DataCopy](data_copy_gm_and_ub_slice.md)（`related`）：《DataCopy》说明软仿接口，支持数据的切片搬运，提取多维Tensor数据的子集进行搬运。；《DataCopy》说明支持GM与UB之间的连续数据搬运，数据传输过程中保持原始格式和内容不变。。二者在切片DataCopy是高维分块搬运的具体重载，连续搬运和数据搬运总览用于界定它的适用边界上存在可执行的直接衔接。
- [DataCopy](data_copy_gm_to_ub_nd2_nz.md)（`related`）：连续 DataCopy 保持布局不变，ND2NZ DataCopy 改变分形格式，二者给出普通连续搬入与格式转换边界。
- [DataCopyPad](data_copy_pad_gm_to_ub.md)（`related`）：连续 DataCopy 依赖 32B 块对齐，GM 到 UB 尾块非对齐时应改 DataCopyPad 并显式填充。
- [DataCopyPad](data_copy_pad_ub_to_gm.md)（`related`）：UB 到 GM 非对齐尾块需用 DataCopyPad 的字节长度语义，补足连续 DataCopy 无法覆盖的搬出边界。
- [PipeBarrier](../../sync_control/intra_core_sync/pipe_barrier_isasi.md)（`related`）：多个 DataCopy 目的地址重叠时需要对应 MTE2 或 MTE3 PipeBarrier 串行化，避免前后搬运覆盖竞态。
- [数据搬运概念（概述）](../../data_move_guide/overview/data_move_concept.md)（`related`）：基础连续搬运类别由该 DataCopy 接口直接实现，count 表达连续元素数。
- [DataCopy](data_copy_gm_and_ub_highdim_split.md)（`same_topic`）：DataCopy 与《DataCopy》的实质衔接是：该 DataCopy 用 DataCopyParams 做 GM/UB 高维切分；slice/continuous 对照、高维 API 分类和 blockLen 窄化故障共同说明何时选用及参数类型边界。
<!-- cannbot:related:end -->
