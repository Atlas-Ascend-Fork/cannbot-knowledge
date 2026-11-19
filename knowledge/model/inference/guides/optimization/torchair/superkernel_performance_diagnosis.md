---
type: Guide
title: SuperKernel 性能劣化：区间耗时、DCCI 与多流串行化
description: 比较同范围 Device 时间而非累加多流算子，区分两后端 DCCI 匹配方式及缓存一致性语义。
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

# SuperKernel 性能劣化：区间耗时、DCCI 与多流串行化

## 版本与任务

依据 TorchAir 固定主线候选 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c`，本卡限定 A2/A3 推理。主线配套尚未确认，不推定 26.0/PyTorch2.8 有相同诊断选项、日志或产物。


## 对齐范围与时间口径

确认 Type=SuperKernel 且成员符合预期后，比较相同输入与范围的 Device 区间。未融合基线使用所有相关流中 max(Start Time+Duration)-min(Start Time)，不要累加彼此重叠的单算子时长。首次编译、Host 下发和同步等待分别度量。

npugraph_ex 可用 ASCEND_PROF_SK_ON=N 观察内部子算子。N 表示每个 core 的 buffer KB，合法 1..5120；0 或未设关闭；实际申请按 64KB 向上对齐，N=1 也会每核申请 64KB。产物为 sk_meta/<pid>/sk_prof_device_{deviceId}.json，子算子区间按最早启动核至最晚结束核统计。它有观测成本，不用开启状态下的耗时冒充正常性能。

## DCCI 需要分别理解两个后端

|后端|配置与匹配|关键限制|
|--|--|--|
|GE 主线静态图|scope 字符串 dcci-before-kernel-start / dcci-after-kernel-end / dcci-disable-on-kernel；按 op_type 精确匹配|不支持正则；来源说明支持 Tiling 下沉或通信类算子时这些选项不生效|
|npugraph_ex 主线|super_kernel_optimize_options 字典，键名使用下划线；按真实符号名匹配，仅支持形如 .* 的格式|符号有前后缀/hash，不能照搬 GE 的纯 op_type 字符串；<<<>>> 与通信算子的内部刷新无法被去除，只能控制外部刷新|

特别注意同名 disable 的语义差异：GE 文档说 dcci-disable-on-kernel 同时取消指定算子 GetValue/SetValue 的自动刷新和外部 DCCI，需自行保证一致性；npugraph_ex 的 dcci_disable_on_kernel 则保留算子内部自动刷新，不插外部 DCCI，且 before/after 优先级更高。后者明确不支持内外两层刷新同时取消。这些配置不能跨后端直接翻译。

GlobalTensor 的 GetValue/SetValue 频繁访问 GM 时，刷新机制可能影响子算子耗时。先二分 scope 定位，再单项切换并复核正确性；不要仅凭性能恢复就证明缓存一致性成立。

## 多流融合可能破坏原有重叠

融合收益主要来自减少调度开销，不自动增加并行度。Cube/Vector 资源互补较有利；两个 Cube、两个 Vector 或 MIX 与其他算子在未占满核数时原本可重叠，融合后却可能因同步保序变为串行。

npugraph_ex 先对照未融合 trace_view.json 与内部子算子时间线，再试 auto_op_parallel=1。GE 查看 te_superkernel*.json 的 DCCI 标记、kernelList，以及 te_superkernel*_kernel.cpp 的子函数调用顺序。调整脚本顺序必须保持所有流内顺序、跨流数据依赖和数值结果；不能为让相邻类型互补而破坏真实依赖。

无法恢复收益时缩小或拆分 scope，或回退关闭该范围融合。每次只改变一个因素，并在关闭调试采集后复测稳态。

- [确认真实融合范围](superkernel_fusion_diagnostics.md)
- [主线同步选项](npugraph_ex_superkernel_sync_controls.md)


## 验证边界

保留相同输入、rank、软件栈和变更前后的证据，先检查输出及存储语义，再关闭调试配置复测。来源案例是定位参考，不能把单条报错视作根因证明。本文仅静态审阅，未执行上游代码或 NPU 实验。

- [软件栈版本与来源身份](../../../concepts/frameworks/ascend_software_stack_baselines.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/superkernel_cases.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/superkernel.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/super_kernel_scope.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

## dcci三选项均未配置时的默认刷新基线

npugraph_ex 主线 superkernel.md 表2（82–84 行）为三个 dcci 选项逐项声明了共同的「均未配置」基线：dcci_before_kernel_start、dcci_after_kernel_end、dcci_disable_on_kernel 都未配置时，子算子内部对 GlobalTensor 的 GetValue/SetValue 默认不自动插入缓存刷新指令，SuperKernel 默认在所有子算子调用后插入 DataCacheCleanAndInvalid 指令刷新 ENTIRE_DATA_CACHE。三选项分别取代该基线：before/after 指定的算子仍不插内部刷新，改由 SuperKernel 在该算子前/后插 DCCI；disable 指定的算子相反——内部默认自动插入刷新、SuperKernel 调用该算子前后不插任何外部 DCCI。此前本卡已载 before/after 优先于 disable、<<<>>> 与通信算子不能去除内部刷新、不支持内外两层刷新同时取消；本节补上「均未配置」基线后 dcci 段承诺配对完整，不把该基线当成任一选项配置后的行为，也不把“所有子算子调用后插入”理解成逐算子插入。发布 pin npugraph_ex/advanced/ 无 superkernel 页（该页 main-only；发布 pin 另有 GE 侧 super_kernel_scope.md 与 api/scope/super_kernel.md，与本节基线无关），该基线不回推 26.0 发布组合。
