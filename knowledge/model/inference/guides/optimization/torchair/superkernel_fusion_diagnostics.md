---
type: Guide
title: SuperKernel 融合诊断：实际范围、sk_meta 与切分原因
description: 用实际 Kernel 与编译产物区分不可融合、Scope 切分及资源不足，分别检查两类后端。
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
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/super_kernel_scope.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
created_at: '2026-11-09T03:19:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# SuperKernel 融合诊断：实际范围、sk_meta 与切分原因

## 版本与任务

依据 TorchAir 固定主线候选 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c`，本卡限定 A2/A3 推理。主线配套尚未确认，不推定 26.0/PyTorch2.8 有相同诊断选项、日志或产物。


## 先证明采集窗口内发生了融合

在 kernel_details.csv 检查 Type=SuperKernel，再从 Name 的 sk_、scope、start_/end_ 片段识别范围。完整名可带 hash、static_kernel 和设备后缀，不应固定完整字符串匹配。没有记录只说明当前已采窗口未观察到融合，还须确认窗口覆盖目标执行和解析有效。

ASCEND_OP_COMPILE_SAVE_KERNEL_META=1 保留编译产物。GE 查看 te_superkernel*.json 的 SuperkernelInfo.kernelList：func_name、sub_operator_op_type、sub_operator_kernel_type、blockNum、streamid；多个文件可能表示范围被拆开。npugraph_ex 查看 sk_meta/<pid>/model_${model_id}_${times}/，不要混用两类产物格式。

## npugraph_ex 的三层原因

|层次|关键线索|下一步|
|--|--|--|
|节点不可融合|NOT_IN_SCOPE、IN_UNFUSIBLE_SCOPE|核对 scope 标记或显式排除|
|节点能力不满足|OP_UNSUPPORT、DYNAMIC_TASK_UNSUPPORT、SIMT_OP_UNSUPPORT|确认实际 Kernel 路线、动态 Task 或 SIMT 限制；不是只看 ATen 名|
|数量限制|EXCEED_CORE_MAX、EXCEED_SCOPE_MAX|核对所需核数、硬件上限和最多 1024 个 scope|
|Scope 被切分|UNFUSIBLE_NODE、DEADLOCK_DETECTED|定位节点或潜在死锁边，核对原始多流时序|
|同步/调试切分|SYNCALL_OP_DROP、DEBUG_PER_OP_MAX_CORE|前者涉及全核同步与核数不匹配，后者是单算子满核调试产生的切分|
|Scope 最终结果|SUCCESS、RESOURCE_INSUFFICIENT|分别表示生成可调度 SuperKernel，或多流融合资源不足；不等于数值或性能验证|

sk_node_detail.log 看初始化后的节点与标记；sk_scope_split.log 看切分；sk_fused_nodes.log 看最终成员；sk_fusion_fail_reasons.log 汇总原因。sk_mdl_origin/updated.json 是前后 Task，sk_graph_origin/updated.json 是前后图节点，sk_task_queue.json 按 AIC/AIV 队列组织；bin_files 的 sk_entry_*.o 为 SuperKernel 二进制。必要时结合 super_kernel.log 和 sk_device_args.log。

## GE 的范围检查

GE 静态 scope 可设 strict-scope-check=bypass 或 abort：前者 Warning 并跳过不符合预期的范围，后者 Error 并终止；plog 搜 super_kernel_scope。检查暂不覆盖 scope 内的集合通信算子，因此未报错不能证明它们均满足融合条件。

GE 多流融合默认关闭；目标范围确有多流且满足约束时核对 stream-fusion=1。原始依赖不变是前提，不为增加融合段数而删除 Event 或控制边。实际融合范围连续也仍不保证收益。

- [后端功能与开启条件](torchair_superkernel_backend_contract.md)
- [执行异常和 COND 定位](superkernel_exception_localization.md)
- [融合后性能分析](superkernel_performance_diagnosis.md)


## 验证边界

保留相同输入、rank、软件栈和变更前后的证据，先检查输出及存储语义，再关闭调试配置复测。来源案例是定位参考，不能把单条报错视作根因证明。本文仅静态审阅，未执行上游代码或 NPU 实验。

- [软件栈版本与来源身份](../../../concepts/frameworks/ascend_software_stack_baselines.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/superkernel_cases.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/superkernel.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/super_kernel_scope.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）
