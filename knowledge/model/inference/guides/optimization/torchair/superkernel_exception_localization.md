---
type: Guide
title: SuperKernel 异常定位：子算子符号、COND 与模型映射
description: 区分 GE 与捕获后端异常日志，按 ModelIdIdx、scopeId 和 opId 定位子算子及同步区间。
tags:
- task.debugging
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/superkernel_cases.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/superkernel.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
created_at: '2026-11-09T03:19:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# SuperKernel 异常定位：子算子符号、COND 与模型映射

## 版本与任务

依据 TorchAir 固定主线候选 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c`，本卡限定 A2/A3 推理。主线配套尚未确认，不推定 26.0/PyTorch2.8 有相同诊断选项、日志或产物。


## 先确认后端和异常范围

GE：plog 的 fault kernel_name 以 te_superkernel 开头时，保存 stream_id/task_id；用 origin_op_name 找用户 scope 及首末算子，再用 symbol 定位子算子函数与相对偏移。不要把整个融合范围名当成实际报错子算子名。

npugraph_ex：查 sk_entry_aic/sk_entry_aiv/sk_entry_mix* 和 Exception is from superkernel function。Callback exception 附近的 kernelDisplayName 描述范围，kernelName 可描述回调定位到的子算子；PrintDfxInfo/SkDfxInfo 提供所有 node、原函数、核数与入口地址。若出现 Found in node[...] 和 Bound SK symbol name，可据 PC 匹配收敛到具体子算子。

## PC 匹配失败时解读 COND

多个相同子算子可能有重复 Origin function name；No sub kernel matched 也不证明子算子都没有执行。结合异常核的 atrace（来源默认 /root/ascend/atrace，实际路径按环境核对）和 AIC_COND/AIV_COND：

|位范围|字段|
|--|--|
|[7:0]|状态：0 未记录有效状态，1 SK 入口启动，2 子算子启动，3 子算子完成，4 SK 入口完成|
|[15:8]|opId，对应子算子序号|
|[31:16]|scopeId|
|[47:32]|ModelIdIdx，运行时注册表索引|
|[63:48]|预留|

ModelIdIdx 不是 sk_meta 目录的真实 ModelId。先用 plog 的 ModelIdIdx→ModelId 映射，再按 scopeId 到 sk_meta/<pid>/model_${model_id}_${times}/sk_task_queue.json 定位队列。AIV_COND=0x103 的含义是 opId=1 的子算子最后记录为完成，不是 model 1 或全部 SuperKernel 已完成。

## 执行轨迹与证据强度

npugraph_ex 可在 super_kernel_debug_options 中设 debug_op_exec_trace=1，前提仍为 static_kernel_compile=True、super_kernel_optimize=True。异常核与所有核的 Sub-kernel running info 可显示 Type/opState/opId。

例如 opState=3,opId=0，下一子算子未启动，只能将问题收敛到两者之间、wait 或同步位置；单个异常核最后状态不足以证明根因。结合所有物理核、外部消息和原始多流依赖，不能通过移除等待或加大全局 timeout 替代修复。

debug_cross_core_sync_check 会隐式启用轨迹；debug_per_op_max_core_num 又会隐式启用前者，并使每个算子独立为一个满核 SuperKernel。它们会改变融合与时序，只用于受控复现；恢复原配置后仍须验收。

- [融合成员及产物](superkernel_fusion_diagnostics.md)
- [同步和激进融合选项](npugraph_ex_superkernel_sync_controls.md)


## 验证边界

保留相同输入、rank、软件栈和变更前后的证据，先检查输出及存储语义，再关闭调试配置复测。来源案例是定位参考，不能把单条报错视作根因证明。本文仅静态审阅，未执行上游代码或 NPU 实验。

- [软件栈版本与来源身份](../../../concepts/frameworks/ascend_software_stack_baselines.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/superkernel_cases.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/superkernel.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）
