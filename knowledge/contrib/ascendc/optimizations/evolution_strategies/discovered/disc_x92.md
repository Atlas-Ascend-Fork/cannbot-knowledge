---
type: Optimization
title: "X92: 跨分支机制合并（sibling diff 再合并）—— 把并行兄弟变体各自已实测的净增量叠进当前最优基座"
description: "做法固定为三步："
tags:
  - task.optimization
  - topic.tiling
  - topic.precision
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# X92: 跨分支机制合并（sibling diff 再合并）

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> schema_version: okf.v1
> kind: discovered_strategy
> id: X92
> title: "X92: 跨分支机制合并（sibling diff 再合并）—— 把并行兄弟变体各自已实测的净增量叠进当前最优基座"
> origin: discovered
> discovered_round: 2
> discovered_from: "8_ConvStandard3d evolution, round_2/parallel_1 (node m1) + round_3/parallel_0 (node m2)"
> base_speedup: "0.34953x -> 0.52354x（m1 = n1+x0 合并，asc-vs-asc -32.45% vs 基线、-10.42% vs n1 且 50/50 例全变快）；再叠 w1 的 host 侧改动 -> 0.54165x（m2，-5.65%）"
> confidence: single_op
> status: active
> op_families: [conv, matmul, cv_fusion, attention, elementwise]
> bottlenecks: [no_overlap, undersize_transfer, launch_overhead]
> tags: [sibling-merge, cross-branch, monotone-improvement, verified-diff, barrier-hoisting, host-dispatch-elimination, parallel-variant-reconciliation, 910b2c, dav-2201]
> strategy_ids: [X92, X39, X52, X75, P10, X26]
> ```

## 判定信号

并行进化一轮跑完后，**多个兄弟变体各自在自己的方向上拿到了实测收益，但它们只共享同一个父基座**——
最优变体通常只包含其中一条分支的改动，其余分支的已验证收益仍是"未兑现"状态。判别特征：

- `world_model.json` 里同一轮的多个 `passed` 节点，其 `solution_ref` 指向同轮不同 `parallel_N`，
  且它们的**改动文件集合几乎不相交**（逐文件 `diff` 各自只有少数几个 net 变更）；
- 最优变体 `X` 的 `strategy_combination` 与次优变体 `Y` 的完全不重叠，但两者的 `parent_solution_ref` 相同；
- 即"收益可加、改动可叠"，而当前最优只吃到了其中一份。

## 核心思路

**把兄弟变体各自已验证的净增量逐项叠进当前最优基座，并且只在"改动集合不相交"处合并。**
做法固定为三步：

1. **取净增量**：对每个兄弟变体，用它自己的实测 `asc-vs-parent` 只保留**已验证有效**的项；
   用逐文件 `diff -u <最优基座>/kernel/<f> <兄弟>/kernel/<f>` 把"净增量"与"基座差异"分开
   （兄弟的基座往往是**更早的分叉**，直接整文件拷贝会把基座带回退）。
2. **对账共享文件**：列出两边都改过的文件，逐行对账；**保留最优基座的语义**，只叠兄弟的净增量。
   典型冲突面：host 侧的 tiling 常量、launch 几何（blockDim）、任务空间与 stride、缓冲区是否 `at::empty`。
3. **验收 = 全量 case 精度 + 同卡同命令的 asc-vs-asc**，与**父基座**比（不要重测父内核浪费一整轮；
   把父基座已有的同卡同口径 `geomean_asc` 直接拿来当 A/B 参考）。

## 实测（8_ConvStandard3d，Ascend910B2C，全量 50 例）

| 合并 | 内容 | asc-vs-asc | 备注 |
|---|---|---|---|
| m1 = n1 + x0 | AIV_ONLY/AIV48/AIC24/epilogue 2D 描述符+乒乓  ⊕  im2col fused-plane + prepare 稠密平面 + gemm L1 双缓冲 | **-10.42%**（50/50 例全变快、0 例变慢） | 三处共享文件对账**无冲突**；`Block Dim 48/48/24/48` 直接验证 |
| m2 = m1 + w1 | 再叠 host 侧 `wp` 单次构造（消 `1+G+(bias?1:0)` 次 aclnn dispatch） | **-5.65%**（36/14 例） | 只改 host；4 个 device 内核与 m1 **逐字节相同** |
| m1_s1 = m1 + gemm 栅栏窗口重排 | 把下一 panel 的 CopyIn 按大小拆开（A 半留在 Split 窗 ∥ MTE1、B 半挪到 Mmad 窗 ∥ MAC） | -1.68%（37/50 例） | 栅栏集合/事件类型/flags **逐字节未变** |

累计：0.34953x → **0.54165x**（相对本轮基线 -36.27%），是本会话**唯一一条连续三轮都为正**的路线。

## 关键坑

1. **兄弟的基座可能更早** —— 整文件拷贝会把基座自身的收益回退掉。必须 `diff` 出净增量。
2. **host 侧语义必须整体保留最优基座的那一份**：本轮 m2 对账时**否决**了 w1 的两处（`AIV_BLOCKS=20`、
   无条件 `at::zeros`），采纳它们会分别回退发射几何与重新引入一个 ZerosLike task。
3. **别重测父内核**：父基座的同卡同口径 `geomean_asc` 已经在它的交付里，直接做分母即可，省一整轮（45-60 分钟）。
4. **收益要按"机制"归因**，不要按"文件"归因：m2 只改 host，但收益来自"每次 aclnn dispatch 是固定 ~10-15us"这一机制。

## 来源

自动发现于 8_ConvStandard3d 进化第 2/3 轮（节点 m1、m2），算子 8_ConvStandard3d，speedup 0.34953x → 0.54165x。
