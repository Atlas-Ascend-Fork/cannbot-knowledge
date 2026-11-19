---
type: Guide
title: TorchNPU Watchdog 与 HCCL 超时：检测和退出边界
description: 说明异步错误处理、当前版本退出例外及 EI0002 的跨 rank 定位顺序。
tags:
- task.debugging
- topic.parallelism
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/fault_diagnosis/watchdog.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/HCCL_timeout.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_ASYNC_ERROR_HANDLING.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_BLOCKING_WAIT.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/HCCL_EVENT_TIMEOUT.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/HCCL_EVENT_TIMEOUT.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_ASYNC_ERROR_HANDLING.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_BLOCKING_WAIT.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/fault_diagnosis/watchdog.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/watchdog_working_principle.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/watchdog_working_principle.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/flight_recorder/flight_recorder.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/tools/flight_recorder/flight_recorder.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/HCCLUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/HCCLUtils.hpp
  role: implementation
created_at: '2026-11-09T02:11:09Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU Watchdog 与 HCCL 超时：检测和退出边界

## 版本与范围

固定 TorchNPU 主线文档，聚焦使用 HCCL 后端的 A2/A3 训练。TORCH_HCCL_ASYNC_ERROR_HANDLING 在 PyTorch1.11 默认 0，≥2.1 默认 1；当前支持旧名 HCCL_ASYNC_ERROR_HANDLING，两者同时配置优先新名。

## 检测不等于所有异常都会退出

Watchdog 在 ProcessGroup 初始化后异步监视集合通信错误、超时和 ERROR CQE。总述描述了停止主进程防止卡住的机制，但更具体的环境变量页限定：当前版本 ERROR CQE 会终止进程，其他错误仅屏显，不会终止。因此不能承诺设为 1 后任何故障都会自动退出。

开启异步处理时，来源建议 init_process_group/new_group 的 timeout 大于 HCCL_CONNECT_TIMEOUT 与 HCCL_EXEC_TIMEOUT，便于先保留 HCCL 的错误信息。连接、执行和框架域超时是不同层次，不能混为一个阈值。

## 超时归因

EI0002 表示等待对端 Notify 超时；报错 rank 可能只是等待方。先汇总所有 rank 的最早异常、退出时间、通信标签与操作顺序，再检查进程退出、慢 rank、样本数/参与不一致及链路丢包。来源案例的根因是一张卡异常退出，不代表所有 EI0002 都是同一原因，也不能仅增大超时掩盖它。

## 验证

核对有效环境变量和完整 rank 日志，区分检测信息与实际进程退出。修复后确认各 rank 操作次序一致、训练继续推进。本次未注入故障、运行通信或验证 Watchdog 退出行为。

## 采证与输入阶段入口

- [状态快照、扩展加载时机和失步分析](torch_npu_hccl_status_capture.md)
- [输入连续性、Socket 建链和 Notify 超时](torch_npu_collective_failure_triage.md)

周期状态记录和超时分析只是观测，不自动终止、重建训练状态或保证恢复。结合所有 rank 的首个异常再选处理路线。

## Host 阻塞等待与 Event 超时

TORCH_HCCL_BLOCKING_WAIT默认0，1使ProcessGroupHCCL的wait/synchronize在Host等待本次通信完成、错误或超时；开启后不创建Watchdog。兼容旧名HCCL_BLOCKING_WAIT，同时设置优先新名，创建进程组时读取，之后修改不影响已有域。因此不能既依赖Watchdog周期状态保存，又不核对阻塞模式是否让该线程根本没有创建。

HCCL_EVENT_TIMEOUT控制Event等待，默认1868秒、范围0..2147483647，0表示不超时；配置时要求大于HCCL_EXEC_TIMEOUT。它与框架域timeout、连接timeout仍是不同层次，不用一个超时值替代所有等待协议。

## Event文档的接口层次与产品表

中英文EVENT页用pyACL说明等待路径：先acl.init，acl.rt.set_op_wait_timeout设置等待时间，后续acl.rt.stream_wait_event任务在该时间内等待、超时返回错误。这里按环境页保留接口层次，不覆盖其外部Runtime库的完整参数，也不证明任意PyTorch等待都等价于这几个调用。

EVENT和BLOCKING_WAIT页列950DT，ASYNC_ERROR_HANDLING页未列950；缺项不等于已证实不支持，也不能把前两项支持扩为整个异步故障处理流程已在950确认。本指南整体保留A2/A3范围，950可消费的环境条目另见[原生集合通信指南](torch_npu_native_collective_constraints.md)。

## 线程图与未给出的版本区间

两语言图已分别查看，展示ProcessGroupHCCL通过std::thread启动hcclCommWatchdog，在workCleanupLoop观察异常并rethrow_exception。开发说明混用“进程/线程”，图内实际线程调用不能据措辞改写成独立watchdog服务进程或所有组共享唯一线程；中文主线程与英文main process标签也不扩大具体退出合同。

总述声称快速检测且不影响训练，属于来源能力描述，本次未验证开销或退出行为；实际ERROR CQE/其他错误差异仍按前文环境页。默认开关只明确PyTorch1.11与≥2.1，未给出的1.12至2.0区间不自行补齐。开启BLOCKING_WAIT不创建Watchdog的分支仍成立。

## 心跳监控是另一个退出路径

主线ProcessGroupHCCL构造处另读TORCH_HCCL_ENABLE_MONITORING（默认false）、HEARTBEAT_TIMEOUT_SEC（600秒）、DUMP_ON_TIMEOUT（false）和TRACE_BUFFER_SIZE（0）。监控读取watchdog的heartbeat_是否推进，处理Work及dump后会增加该计数；工具文档把它简写为“训练多久未下发collective”，不能等同一个直接量测Python调用间隔的计时器，也不据此保证业务空闲一定不会触发。

已读心跳分支在无进展时请求dump、保留best effort采证，等待和正常退出分支之后，若监控仍启用且尚未终止，可走terminateProcess的FATAL/abort。这与前文环境页所述普通异步错误屏显/CQE退出不是同一个条件，不能据“其他错误仅屏显”概括为任意心跳异常都不会退出。实际线程创建、编译条件、BLOCKING_WAIT和各开关仍共同决定路径。

dumpDebuggingInfo先尝试Python线程栈、等待GIL至3000ms，再按trace buffer和writer条件落盘；“Could dump”日志或返回值不独立证明每个文件均写成功。飞行记录器分析的限制见[离线工具草稿](torch_npu_flight_recorder_analysis.md)，本次没有故障注入、等待、dump或终止进程。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/fault_diagnosis/watchdog.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/HCCL_timeout.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_ASYNC_ERROR_HANDLING.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_BLOCKING_WAIT.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/HCCL_EVENT_TIMEOUT.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/HCCL_EVENT_TIMEOUT.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_ASYNC_ERROR_HANDLING.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_BLOCKING_WAIT.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/fault_diagnosis/watchdog.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/watchdog_working_principle.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/watchdog_working_principle.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/flight_recorder/flight_recorder.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/tools/flight_recorder/flight_recorder.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/HCCLUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/HCCLUtils.hpp)（implementation）
