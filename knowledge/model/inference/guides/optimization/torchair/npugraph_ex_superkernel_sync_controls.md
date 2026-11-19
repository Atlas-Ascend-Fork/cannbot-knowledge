---
type: Guide
title: npugraph_ex SuperKernel 同步选项：Early-Start 与 ValueWait 融合
description: 解释需算子内适配的提前启动、激进融合位掩码及多重匹配失败，不把配置存在视为同步正确。
tags:
- task.debugging
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/superkernel.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
created_at: '2026-11-09T03:19:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# npugraph_ex SuperKernel 同步选项：Early-Start 与 ValueWait 融合

## 版本与任务

依据 TorchAir 固定主线候选 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c`，本卡限定 A2/A3 推理。主线配套尚未确认，不推定 26.0/PyTorch2.8 有相同诊断选项、日志或产物。


## 前提

本卡只解释固定主线的选项；需同时开启 static_kernel_compile 和 super_kernel_optimize。GE scope 的字符串 options 是另一套接口。先使用默认保守融合，确认真实 scope、依赖、输出与原地状态后再评估局部选项。

## 提前启动依赖算子内适配

super_kernel_optimize_options 的 early_start 默认 0，设为 1 后识别并生效算子中已适配的 AscendC::SetNextTaskStart()/WaitPreTaskEnd()，可使下一任务头部 Scalar 指令提前执行。没有算子内适配不能仅凭此开关宣称提前执行或获得收益。本卡未生产这些 Ascend C/Runtime API 的完整源码契约。

## 激进融合不等于忽略所有依赖

aggressive_opt_strategies 是字典，task_breaker_bypass 默认 0：遇非 AICore Task 时断开。设 1 仅在该流范围内没有其他 AICore 算子时，可剔除非 AICore Task 而不切断融合范围，不是将 AICPU Task 变成可融合 AICore 算子。

value_breaker_bypass 默认 0b00，按位选择 ValueWait 节点：

|值|允许进入融合的节点|
|--|--|
|0b00|不融合 ValueWait|
|0b01|已与 ValueWrite 按 Flag 规则配对，且通过死锁检测的 ValueWait|
|0b10|没有对应 ValueWrite 的未配对 ValueWait|
|0b11|上述两类|

同一 ValueWait 被多个 ValueWrite 匹配会触发 SuperKernel 报错，导致整体融合失败；未配对并不证明等待来源不存在，可能来自融合范围外。Flag 的完整匹配、运行时信号与内存顺序须另核对，不能从位掩码推导这些前提已满足。

## 保留可回退的比较

记录默认策略的切分原因、事件图和执行结果，再逐项尝试；若出现 DEADLOCK_DETECTED、等待不前进或多重匹配错误，回到保守策略检查依赖。固定选项和图结构均不能替代多次 Replay、不同输入状态和跨流顺序的实际验证。

- [融合原因与 Scope 切分](superkernel_fusion_diagnostics.md)
- [图内 Event 与控制边](graph_multistream_dependencies.md)


## 验证边界

保留相同输入、rank、软件栈和变更前后的证据，先检查输出及存储语义，再关闭调试配置复测。来源案例是定位参考，不能把单条报错视作根因证明。本文仅静态审阅，未执行上游代码或 NPU 实验。

- [软件栈版本与来源身份](../../../concepts/frameworks/ascend_software_stack_baselines.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/superkernel.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）
