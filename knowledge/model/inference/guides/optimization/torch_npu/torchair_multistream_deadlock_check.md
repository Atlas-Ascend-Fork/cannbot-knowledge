---
type: Guide
title: TorchAir 多流死锁检测：AIV 资源冲突与诊断边界
description: 说明主线 GE/捕获后端的检测入口、动态限制和风险报告，避免视为自动修复。
tags:
- task.debugging
- topic.parallelism
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/deadlock_check.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/deadlock_check.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
created_at: '2026-11-09T02:14:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchAir 多流死锁检测：AIV 资源冲突与诊断边界

## 版本与范围

仅依据 TorchAir 主线 92e1e967bd35ebc37a442b4a969730bf3cf77a3c，A2/A3 推理。固定发布子模块没有对应功能页，不宣称发布版可用。未做设备死锁复现。

## 触发与检查

多个流上的通信任务同时就绪，所需 AIV 总和超过可用资源时，可能互相等待而形成资源死锁。GE 设置 config.debug.deadlock_check=True，明确不支持 dynamic=True；npugraph_ex 用 options.deadlock_check=True，按其后端说明核对支持范围，不能将 GE 的动态图限制自动推广成另一后端的声明。

风险报告包括原图、过滤计算算子后的图和 *_filtered_deadlock_check.json，并输出冲突 stream/task、请求核数与总资源。文档示例 32+24>48 是特定设备的例子，不能将 48 写成所有 SoC 的硬件常量。

## 定位与验证

将冲突任务映射回模型的集合通信、流、核数配置与参与 rank；调整时须同时保留通信顺序和真实数据依赖，再重新检测并观察运行推进。检测用于提示资源冲突，不自动修复，也不证明没有其他等待环、rank 不一致或网络故障。

- [执行和生命周期依赖](../torchair/graph_multistream_dependencies.md)
- [控核和确定性](../torchair/torchair_core_limits_and_determinism.md)
- [HCCL 超时与 Watchdog](../../../../training/guides/torch_npu_hccl_watchdog_timeout.md)


## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/deadlock_check.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/deadlock_check.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）
