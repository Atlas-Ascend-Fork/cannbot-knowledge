---
type: Runbook
title: 图捕获安全策略：global、thread_local 与 relaxed 定界
description: 定位 npugraph_ex 捕获期不安全操作报错，解释 capture_error_mode 的检查范围及放宽检查的验证边界。
tags:
- task.debugging
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/capture_error_mode.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
created_at: '2026-11-08T11:58:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 图捕获期操作的检查范围

## 症状与探针

npugraph_ex 在捕获期间因设备内存分配等可能不安全操作报错时，先记录操作、线程、捕获区间和 options.capture_error_mode。确认是捕获阶段报错，而非后续执行或内存不足。

## 三种配置

global 是默认值，对当前线程和其他线程的相关操作报错；thread_local 只检查当前线程；relaxed 不对这些操作报错。该配置最终交给 torch_npu.npu.graph 上下文，改变的是检查范围。

## 处置与验证

优先把可移出的动态分配或主机操作移至捕获外，再用相同输入重试。为定界选择其他模式时，保留原始 global 行为和修改范围；取消报错不能证明该操作具备图捕获安全性。必须比较 Eager、首次捕获与重复重放的输出和地址/状态稳定性。

仍不能确认安全时恢复 global，缩小捕获边界或退回 Eager。本文是固定主线文档导出的诊断路径，没有复现日志或设备测试，不宣称已修复具体故障。

## 版本入口

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)：来源快照、部署配套和实际运行验证分别核对。

## Evidence

- [docs/zh/npugraph_ex/basic/capture_error_mode.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/capture_error_mode.md)（primary）
- [docs/zh/overview.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）
