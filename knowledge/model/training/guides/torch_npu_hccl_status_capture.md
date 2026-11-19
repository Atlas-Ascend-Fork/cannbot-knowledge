---
type: Guide
title: HCCL 状态采证：加载前配置、周期快照与失步分析
description: 记录状态文件读取时机、默认间隔和 rank 身份，不把超时分析开关误作自动恢复。
tags:
- task.debugging
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_ENABLE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_PATH.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_INTERVAL.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_DESYNC_DEBUG.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_DESYNC_DEBUG.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_ENABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_INTERVAL.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_PATH.md
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
created_at: '2026-11-09T03:52:43Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# HCCL 状态采证：加载前配置、周期快照与失步分析

## 版本与范围

依据固定 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的四个环境变量页，按各页明确支持的A2/A3训练系列及950DT条目处理。配置时机与旧名兼容属于该提交，不回推所有版本。

## 在扩展加载前设置状态采集

TORCH_HCCL_STATUS_SAVE_ENABLE 默认 0，设 1 后由 Watchdog 周期保存 collective 的 seq、op_type、pg_id、comm_ids、status，并在 Watchdog 异常退出时追加错误状态。ENABLE 与 PATH 在 ProcessGroupHCCL.cpp 全局初始化时读取，应在加载 torch_npu 扩展前设置；在已 import 的训练进程里临时修改不保证生效。

PATH 默认 /tmp，仅 ENABLE=1 才写入。文件名包含 global_rank、master_addr、deviceId、numRanks、pid、timestamp，分析时不能将另一进程或重启后的文件当作当前作业。

STATUS_SAVE_INTERVAL 默认 2s，≤0 重置为 2；首次读取后缓存。它是保存周期，不是通信超时阈值。周期快照可能遗漏两个采样点之间的转换，不能把最后一条 status 视为所有 rank 的完整因果轨迹。

## 失步分析的边界

TORCH_HCCL_DESYNC_DEBUG 默认 0，兼容 HCCL_DESYNC_DEBUG，两者同时配置优先新名。所查页面说明当前只打印超时分析结果，不负责终止进程；大集群开启还可能出现卡死，需要小范围受控使用。PyTorch1.11 的配套条件要求同时开启异步错误处理，不能把这条旧版条件无区别套给所有版本。

分析时按通信组、序号和操作类型对照所有 rank，并寻找最早异常；发现各 rank 停在不同位置是线索，不直接证明网络故障，也不表示已经恢复。

## 核验

检查真实环境加载时点、目录写入、文件身份和实际保存节奏；修复后确认各 rank 持续推进。没有生成文件时先查开关和加载时机，不把它解释成“通信没有异常”。本文未运行故障注入或通信。

- [Watchdog 检测与退出](torch_npu_hccl_watchdog_timeout.md)
- [输入、建链和执行分阶段诊断](torch_npu_collective_failure_triage.md)

## 950DT条目与Watchdog前提

四份中英文环境页均列A2/A3及950DT，以上保存时机、间隔和失步分析条件按这些条目适用。文件名的准确格式为`torch_hccl_status-<global_rank>_<master_addr>_<deviceId>_<numRanks>_<pid>_<timestamp>.log`。状态保存依赖Watchdog，开启TORCH_HCCL_BLOCKING_WAIT后不创建该线程，不能要求同时得到同一条Watchdog周期采证路径。

三个STATUS_SAVE变量由TorchNPU提供，来源说明PyTorch没有直接对应变量；DESYNC_DEBUG的旧名兼容单独处理，不把原生NCCL变量当自动别名。失步诊断在大集群可能卡死、仅打印不终止的边界仍保留；本次未创建日志文件或注入故障。

## 周期status日志与飞行记录器dump不是同一产物

tools/flight_recorder分析的是各rank的二进制trace及pg_config/entries/schema version，不是本卡torch_hccl_status-*.log的直接读取器。主线默认dump writer采用前缀+global rank、会覆盖同名文件；Python线程栈另有_py_traceback后缀，不能将这三类输入混用。

该离线工具的命名/解析和错误报告存在静态缺口，详见[飞行记录器草稿](torch_npu_flight_recorder_analysis.md)。状态采证本身的950DT范围不代表这个分析器所有路径已在950验证，本次未读取dump或运行解析。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_ENABLE.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_PATH.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_INTERVAL.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_DESYNC_DEBUG.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_DESYNC_DEBUG.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_ENABLE.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_INTERVAL.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_PATH.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/flight_recorder/flight_recorder.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/tools/flight_recorder/flight_recorder.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/HCCLUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/HCCLUtils.hpp)（implementation）
