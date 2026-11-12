---
type: Guide
title: SuperKernel 范围分析：依赖边界、受控基线与融合验证
description: 从模块、整层到跨层选择 SuperKernel scope，识别动态控制流和分流控核边界；在相同 GE 配置下比较预热后的中位数、波动、编译产物和精度。
tags:
- task.optimization
- topic.graph_execution
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-superkernel/references/scope-analysis-guide.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-superkernel/references/performance-baseline-guide.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/common_utils.py
  role: supporting
created_at: '2026-11-10T03:39:02Z'
updated_at: '2026-11-10T03:54:53Z'
platforms:
- a3
aliases:
- SuperKernel 基线验证
- SuperKernel 跨方法范围
- SuperKernel scope 调优
---

# SuperKernel 范围分析与受控验证

## 适用范围

用于固定 Recipes 的 Atlas A3、TorchAir GE SuperKernel 候选范围分析与验证。当前 R1/LongCat 的实际模型门控见 [范围决策](../../optimizations/rules/superkernel_decode_ge_graph_fusion_scope.md)；本文不把旧 LLaMA/Qwen 模板当成这些模型在所有后端均可部署的证据。这里保存分析方法，不复制外部 Agent 工作流。

## 分析范围与依赖

先区分 host 下发、kernel 间等待、计算和通信瓶颈，查看图与时间线；不能将所有慢模型都归因于 scope 太小。范围过小可能保留较多调度边界，范围过大可能跨越不支持算子、流切换或控核边界，造成编译失败或资源竞争。没有适用于所有模型的固定层数。

可从最小可行模块开始，逐层扩大范围；也可先验证较大候选，编译或精度失败后逐段缩小。每次只改变一个范围并保存结果。Attention、MLP/MoE、整层、跨层都是候选，编译器支持与真实数据依赖决定能否采用，不能单凭 Python 方法边界决定。

跨方法 scope 要确认同一条有效执行路径、完整依赖和算子支持。区分可展开的静态层循环与依赖运行时数据的动态控制流；当前 R1 可包住多层 Decode，故不能从旧模板“避免 if/for”推出所有静态 for 都禁止。Prefill/Decode 的合法范围按各模型门控核对，不能复制 Decode 的开关到 Prefill 后认定已生效。

## 受控基线与比较

保留原始配置并复制候选基线，仅切换 `enable_superkernel`，保持 GE 后端、模型、真实权重、负载、并行度及其余优化开关一致。确认开关确实到达模型 scope helper；切换后检查编译产物与编译缓存，不将切到 eager 当成仅关闭 SuperKernel。

两组分别完成目标形状预热，首次编译时间单列，稳态 Decode 采用同一统计窗口。对比 Decode 单步耗时的中位数、重复样本波动、吞吐、峰值显存和精度，并结合任务调度与通信时间线解释变化。Profiler 用于定位，最终时延用关闭 profiler 的同条件测量；多流 kernel Duration 不能简单相加成 wall time。

旧材料的固定重复次数、波动百分比和收益阈值是示例口径，不是普遍验收线。保留样本数量、统计方式、软件版本和输出，不能用一次最快结果证明收益，也不能把叠加其他优化后的整网速度当成 SuperKernel 单项收益。

## 编译失败、静默未生效与回退

编译失败时缩小范围并定位不支持算子、动态分支、跨流依赖或布局边界。能执行但没有预期融合时检查实际成图和融合产物；写出 scope 并不保证全部算子融合。性能劣化时先核对负载、预热与资源竞争，恢复原 scope/配置及匹配缓存，并重新验证输出。

源码事实与指南示例分开记录。本文未执行 NPU 编译或性能测量，不新增硬件验证结论。


## 比较条件判定

| 场景 | 可归因单项收益 | 核对方式 |
| --- | --- | --- |
| same_ge_one_switch | yes | 同一 GE 路径只改变 enable_superkernel，并完成预热和输出验证 |
| eager_vs_ge | no | 同时改变执行后端，不能只归因于融合 |
| compile_in_steady_window | no | 首次编译混入稳态窗口，应分报冷启动 |
| multiple_changes | no | 同时改变并行度、量化或多流，不能归因单项 |
| scope_marker_only | no | 只有源码标记，仍需检查成图、融合和实际时延 |
| static_layer_loop | needs_graph | 静态层循环须核对编译结果，不一概禁止 |
| dynamic_data_branch | needs_graph | 运行时数据分支须核对捕获与图合法性 |


## Evidence

- [固定来源](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-superkernel/references/scope-analysis-guide.md)（primary）
- [固定来源](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-superkernel/references/performance-baseline-guide.md)（supporting）
- [固定来源](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py)（supporting）
- [固定来源](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/common_utils.py)（supporting）
