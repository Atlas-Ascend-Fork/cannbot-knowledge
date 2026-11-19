---
type: Guide
title: TorchNPU TaskQueue：下发级别与每流队列
description: 说明三级下发、独立 workspace 池、aclgraph 不兼容及每流队列的实验限制。
tags:
- task.optimization
- topic.performance.analysis
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/taskqueue/taskqueue_parallel_delivery.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/taskqueue/stream_taskqueue_parallel_delivery.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/TASK_QUEUE_ENABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/PER_STREAM_QUEUE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/TASK_QUEUE_ENABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/PER_STREAM_QUEUE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/ASCEND_LAUNCH_BLOCKING.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/ASCEND_LAUNCH_BLOCKING.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/stop_task_queue.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/stop_task_queue.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/Level-1.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/Level-1.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/Level-2.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/Level-2.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/taskqueue/taskqueue_parallel_delivery.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/taskqueue/stream_taskqueue_parallel_delivery.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/taskqueue_parallel_delivery_fig_01.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/taskqueue_parallel_delivery_fig_01.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/taskqueue_parallel_delivery_fig_02.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/taskqueue_parallel_delivery_fig_02.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/taskqueue_parallel_delivery_fig_03.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/taskqueue_parallel_delivery_fig_03.png
  role: constraint
created_at: '2026-11-09T02:11:09Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU TaskQueue：下发级别与每流队列

## 版本与范围

依据 PyTorch 固定主线 ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，聚焦 A2/A3 的 Host 下发。不是 26.0 发布支持声明，也没有设备性能验证。

## 机制与选择

TASK_QUEUE_ENABLE=0 在调用线程串行下发；默认 1 将主要 aclnn Host API/launch 迁移到二级流水线程，workspace 仍在主线程申请；2 进一步迁移 workspace 计算与申请，使用独立池，可能提高峰值内存。环境变量页还限定 Level2 仅二进制场景生效。

Level2 与 NPUGraph/aclgraph 不兼容。非内置自定义算子不能直接采用 Level2，必须核对接入要求；Level1 的自定义算子也需要适配。ASCEND_LAUNCH_BLOCKING=1 会关闭队列，使此设置不生效。

默认同设备所有线程和 Stream 共用队列。跨流等待若先入队、被等待任务滞留队尾，会形成队头阻塞甚至死锁；必须保证多线程下发的依赖顺序，不能仅凭 Stream 数量推定并行。

## 每流队列

PER_STREAM_QUEUE=1 为每个流创建独立 TaskQueue/Dequeue 线程，默认 0，且依赖 TASK_QUEUE_ENABLE=1 或 2。当前为实验特性，只在多线程多流且 Dequeue 阻塞时考虑。它不支持进程级在线恢复、细粒度绑核；额外线程会竞争资源，跨流 Event 的保序还可能增加一级流水耗时。非默认流 OOM 不会立即触发快照。

## 验证

先采集 Host 下发与 Device 空洞，再在相同模型输入、通信顺序下比较配置的稳态耗时和峰值内存。检查跨流依赖、实际环境变量和运行模式；来源的延迟收益不能当作本地保证。仅静态核对。

- [分配器选项](../torch_npu_allocator_options.md)
- [OOM 内存快照](torch_npu_oom_memory_snapshot.md)


## 配套接入与诊断

- [自定义算子的标准宏和底层回调接入](torch_npu_custom_op_taskqueue_adaptation.md)
- [异步错误栈、队列清空与设备同步](torch_npu_taskqueue_error_and_flush.md)

## 同步调试与流水图的核对

ASCEND_LAUNCH_BLOCKING默认0异步，1同步可显示实际调用栈但降低性能，并覆盖TASK_QUEUE_ENABLE关闭队列；0的并发会增加内存消耗及OOM风险，不把调试同步后的耗时作为正常吞吐。中英文三张图已分别查看：关闭队列时torch.add、workspace计算/申请、aclnnAdd都在主线程；Level1只把aclnnAdd移至二级流水；Level2连workspace计算/申请一起移动。图示没有表达所有算子都获益，也没有给设备性能测量。

TASK_QUEUE_ENABLE、PER_STREAM_QUEUE和同步调试环境页均列950DT；本卡的Level2图模式兼容、自定义接入和细粒度绑核等开发说明范围独立保留，不能由环境页支持把完整组合扩到950。每设备默认共享队列时仍需保证跨线程依赖下发顺序，每流队列也不消除业务数据依赖。

## 开发页三幅图的准备与释放阶段

已分别查看两语言六幅图：Level0所有准备、aclnn执行和包装释放在主线程；Level1在主线程准备workspace与aclTensor，入队aclnn/地址/stream，出队线程执行并释放aclTensor；Level2主线程只保留类Tensor对象准备，将workspace申请、aclTensor构造、执行和包装释放一起移到下发线程。释放aclTensor包装不等于释放业务Tensor设备存储。

开发页同设备所有线程/Stream共享一队列，不同设备和不同进程独立。其典型下发延迟降低5%至20%是来源场景描述，不是端到端吞吐承诺；Level2独立workspace池仍可能提高峰值内存。开发页笼统称1/2模式适配后可受开关控制，不能覆盖环境页对二进制场景、非内置Level2、NPUGraph的更窄限制；完成通用回调接入不单独证明Level2组合可用。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/taskqueue/taskqueue_parallel_delivery.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/taskqueue/stream_taskqueue_parallel_delivery.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/TASK_QUEUE_ENABLE.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/PER_STREAM_QUEUE.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/TASK_QUEUE_ENABLE.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/PER_STREAM_QUEUE.md)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/ASCEND_LAUNCH_BLOCKING.md)（primary）

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/ASCEND_LAUNCH_BLOCKING.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/stop_task_queue.png)（constraint）

- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/stop_task_queue.png)（constraint）

- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/Level-1.png)（constraint）

- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/Level-1.png)（constraint）

- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/Level-2.png)（constraint）

- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/Level-2.png)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/taskqueue/taskqueue_parallel_delivery.md)（constraint）

- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/taskqueue/stream_taskqueue_parallel_delivery.md)（constraint）

- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/taskqueue_parallel_delivery_fig_01.png)（constraint）

- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/taskqueue_parallel_delivery_fig_01.png)（constraint）

- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/taskqueue_parallel_delivery_fig_02.png)（constraint）

- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/taskqueue_parallel_delivery_fig_02.png)（constraint）

- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/taskqueue_parallel_delivery_fig_03.png)（constraint）

- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/taskqueue_parallel_delivery_fig_03.png)（constraint）
