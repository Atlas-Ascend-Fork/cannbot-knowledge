---
type: Guide
title: TaskQueue 定位：异步栈偏移、队列清空与 Device 同步
description: 区分 Host 下发完成和设备执行完成，说明 stream 查询隐式清空及 Event 不清空时的阻塞。
tags:
- task.debugging
- topic.performance.analysis
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/taskqueue/faq.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/TASK_QUEUE_ENABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/ASCEND_LAUNCH_BLOCKING.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/taskqueue/faq.md
  role: constraint
created_at: '2026-11-09T02:56:52Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TaskQueue 定位：异步栈偏移、队列清空与 Device 同步

## 版本与范围

依据固定 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`，A2/A3。只读来源分析，未注入故障或测量开销。

## 异步报错栈

TASK_QUEUE_ENABLE=1/2 会把 Host API 错误与主线程调用点解耦。定位 aclnn Host API 可关闭 TaskQueue；定位 Device Kernel 可用 ASCEND_LAUNCH_BLOCKING=1 加强同步。定位配置会改变执行节奏，不能把它的耗时或“未复现”直接当成原异步路径结论。

## 清空不等于计算结束

清空表示 CPU 队列中的任务已完成下发，不一定完成 Device 执行。stream()、stream(true) 和 NPUStream 的隐式转换可能清空；显式 stream(false) 不清空，但必须保证真实 Kernel launch 仍经过正确入队顺序。

固定指南列出 Stream.npu_stream、__repr__、__hash__、Stream.query、限核设置、内存池设置、empty_cache、tensor.item、捕获开始等会触发清空。打印流对象或循环查询可能改变 Host 性能，先检查观测本身是否引入同步。

current_stream/default_stream 获取对象、Event.record/query/synchronize 不清空整队列，但 Event.query 在记录尚未下发时可返回 False；Event.synchronize 仍会等待相应记录下发。不能把“不清空”解释成“永不阻塞”或“设备计算已经结束”。

## 验证

保留相同输入的队列开关、同步设置和各 rank 首个错误；用时间线核对下发与设备执行。修复后恢复原异步设置复测，避免依靠调试同步掩盖跨流或生命周期问题。

- [异步接入与原始指针前提](torch_npu_custom_op_taskqueue_adaptation.md)

## 同步定位的环境开销

ASCEND_LAUNCH_BLOCKING 默认 0 为异步，设 1 强制同步以更准确地把设备错误对应到调用栈，并关闭 TaskQueue；不是可用于正常性能比较的设置。默认异步也可能增加内存并导致 OOM，所以同步后不再 OOM 或不复现时，仍应检查并发内存与依赖，不据此认定问题已修复。

## 完整FAQ的清空分组

固定中英文FAQ的20个触发项和11个不触发项按组整理如下；表中对象简写用于检索，FAQ里的torch.npu._C路径不据此保证是安装版本可执行的模块路径，实际绑定命名仍核对torch_npu._C。

| 行为 | 本页列出的接口 |
| --- | --- |
| 清空并承担相应同步语义 | npu.synchronize、Stream.synchronize、Tensor.item |
| 获取/查询流时清空 | getCurrentRawStream、Stream.npu_stream、Stream._as_parameter_、Stream.__hash__、Stream.__repr__、Stream.query |
| 其他清空入口 | set_stream_limit、reset_stream_limit、Event.elapsed_time、Event.recorded_time、ExternalEvent.reset、memory._set_allocator_settings、empty_cache、empty_virt_addr_cache、finalize_dump、set_op_timeout_ms、graphs.graph.__enter__ |
| 不清空的设备/流入口 | set_device、current_device、device_count、set_stream、current_stream、getCurrentRawStreamNoWait、default_stream |
| 不清空的事件/捕获入口 | Event.record、Event.query、Event.synchronize、graphs.graph.__exit__ |

Event.query在record尚未下发时直接False，已下发后查询runtime状态；Event.synchronize不清空整队列却仍等待相应记录下发，不能据此断言不等待设备。设备/流同步要求下发和相应执行完成，普通flush只保证下发；NoWait句柄绕过等待也不取消调用者的顺序责任。

错误对照表将Python/ATen两端都列准确，Host API在GPU列准确而NPU队列模式列不准确，Device kernel两端异步均不准确。故Host定位先关队列，设备定位再强制同步；不把两种错误归因混为一次开关实验。本次未执行接口、注入错误或测量清空耗时。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/taskqueue/faq.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/TASK_QUEUE_ENABLE.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/ASCEND_LAUNCH_BLOCKING.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/taskqueue/faq.md)（constraint）
