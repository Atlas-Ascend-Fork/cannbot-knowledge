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

- [DataCopy](data_copy_gm_and_ub_highdim_split.md)（`same_topic`）：当高维参数退化为连续访问时，以“连续搬运场景推荐使用 DataCopy GM 与 UB 连续数据搬运接口以获得更好性能。”作选型触发，并用“支持GM与UB之间的连续数据搬运，数据传输过程中保持原始格式和内容不变。”确认连续接口保持格式和内容不变，从而减少不必要的高维配置开销。
<!-- cannbot:related:end -->
