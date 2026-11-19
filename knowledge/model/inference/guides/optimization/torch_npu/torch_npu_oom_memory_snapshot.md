---
type: Guide
title: TorchNPU OOM 内存快照：历史、路径与版本限制
description: 区分快照当前状态、历史事件和组件 CSV 的支持条件，保留每流队列触发限制。
tags:
- task.debugging
- topic.memory
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/memory_snapshot.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/OOM_SNAPSHOT_ENABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/OOM_SNAPSHOT_PATH.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/taskqueue/stream_taskqueue_parallel_delivery.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/memory.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/OOM_SNAPSHOT_ENABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/OOM_SNAPSHOT_PATH.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/memory_management/memory_snapshot.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/memory_usage.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/memory_usage.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/memory_allocator_status_history.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/memory_allocator_status_history.png
  role: constraint
created_at: '2026-11-09T02:11:09Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU OOM 内存快照：历史、路径与版本限制

## 版本与范围

依据固定 TorchNPU 主线文档，选取来源明确支持的 A2/A3。快照基本功能要求 TorchNPU≥6.0.0；OOM 组件 CSV 另要求 Ascend HDK≥25.5.0、CANN 商用≥8.5.0。不能把基本快照的最低版本用于 CSV。

## 采集与解释

OOM_SNAPSHOT_ENABLE 默认 0；1 在 OOM 时保存当前及历史分配/释放信息；2 只保存当前状态。OOM_SNAPSHOT_PATH 未配置时为当前目录，配置时路径必须存在且运行进程可写，并需配合 ENABLE 使用。

任意时刻可先调用 torch_npu.npu.memory._record_memory_history() 记录历史，再在目标步骤调用 _dump_snapshot("my_snapshot.pickle")。快照可用 memory_viz 查看分配块、堆栈与 allocator 事件；它与组件实时/峰值 curMemSize、memPeakSize 的 CSV 是不同产物。字段结构可能随版本改变，不能假设与社区 CUDA 快照完全相同。

TASK_QUEUE_ENABLE=2 可额外观察独立 workspace 池的使用；PER_STREAM_QUEUE 开启后，非默认流队列的 OOM 不会立即触发快照，缺少文件不能证明未发生 OOM。

## 验证

核对同一进程/rank 的路径、时间、采集模式及版本，区分已分配、缓存保留和组件峰值；需要历史归因时不能只采模式 2。本次未触发 OOM 或运行设备采集。

- [内存计数器口径](torch_npu_memory_counters.md)
- [训练框架的周期快照配置](../../../../training/concepts/techniques/training_debug_observability.md)


## 预防拒绝不会触发自动快照

固定主线的throw_on_npumalloc_oom=True在达到条件时直接拒绝申请，增加num_oom_rejections，但该路径不触发OOM_SNAPSHOT_ENABLE。应结合实际分配器选项、计数器和异常判断，不能用缺失快照排除内存申请失败；具体门槛和配额冲突见[内存调试与拒绝路径](torch_npu_memory_debug_and_rejection.md)。

## 手动导出的参数与采样副作用

原生接口与固定memory.py的复核另见[NPU内存API指南](torch_npu_native_memory_api_scope.md)：池snapshot、全局memory_snapshot与私有_snapshot返回层次不同，device参数接线和_dump_snapshot的组件导出/Profiler后备路径应单独核对。自动OOM触发、历史开关和本卡版本门槛继续独立消费，不由手动导出接口清单扩展950自动采集范围。

## 图示中的时间线与分配器事件

两语言快照PNG逐字节相同，已查看：第一张以时间为横轴、占用为纵轴，彩色分配块可对应调用栈；第二张按左侧alloc/free事件选择分配器状态，右侧显示segments中的已分配和空闲块。截图里的约22G、地址、stream及历史代码路径都是样例，不作为本机容量、活跃指针或本次运行结果。

需要历史归因时先记录history；只查看当前状态不等于已经得到事件全过程。组件CSV的curMemSize/memPeakSize是另一份产物，其HDK/CANN门槛不能被基本快照TorchNPU≥6.0替代；TASK_QUEUE=2的workspace、默认/非默认流与预防拒绝的触发边界仍各自成立。没有导出、加载pickle或打开外部查看器。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/memory_snapshot.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/OOM_SNAPSHOT_ENABLE.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/OOM_SNAPSHOT_PATH.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/taskqueue/stream_taskqueue_parallel_delivery.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/memory.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/OOM_SNAPSHOT_ENABLE.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/OOM_SNAPSHOT_PATH.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/memory_management/memory_snapshot.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/memory_usage.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/memory_usage.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/memory_allocator_status_history.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/memory_allocator_status_history.png)（constraint）
