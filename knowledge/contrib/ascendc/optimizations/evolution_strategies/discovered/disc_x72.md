---
type: Optimization
title: "掩码来源分析削减向量管计算（全 1 快路径 + 对角三角跳过 + S 广播融合）"
description: "纯向量 AIV 注意力（Cube 不可用）的瓶颈是向量管计算饱和；对掩码来源做静态分析，跳过可证明为全 1 或三角的 tile，并融合 S 广播/归约以削减向量计算。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.reduction
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# X72: 掩码来源分析削减向量管计算

## 核心思路
纯向量 AIV 注意力（Cube 不可用）的瓶颈是向量管计算饱和（aiv_vec_ratio 高）。
对**掩码的来源做静态分析**，识别"掩码可证明为全 1 / 三角"的 tile，直接跳过对应
向量计算；同时对 S 广播/归约做融合削减。三项技术全部位精确（`x·1.0=x`）：

1. **全 1 掩码快路径**（ComputeV1）：当 tile 掩码恒为 1（无 mlen 窗口、整 tile
   全历史列 `col < n-nt`、非因果或因果下非对角线 `t<qbLocal`、非尾块 `kvRows=64`）
   时，跳过整个 per-row 掩码循环（多条向量指令 + 每行一次 GetValue），仅用单条
   `Muls(sUb, kvUb, 1.0f)` 拷贝。大 shape 下多数 tile 可命中。
2. **对角 tile PV 三角跳过**（ComputePV）：因果且无 ctx/mlen 的对角线 tile
   （`t==qbLocal`）掩码为三角（`j<=i`），跳过 `j>i` 的 Axpy（`0*v=0` 位精确），
   省对角线 tile 一半 PV。
3. **S 广播+乘融合**（ComputeS）：父代 `2-pass`（按 tile 行数逐行 Adds 广播 +
   1 次整块 Mul）改为单次 per-(i,j) `Mul(red[j], qRow, kvUb[j])`，S 向量指令显著
   减少，并消掉 Adds→Mul 的 PIPE_V 屏障。kvUb 尾行/填充已清零 → 尾 j 行
   `red=qRow*0=0`、ReduceSum 尾列恒 0，精度不变；D 非 16B 对齐时对 red 填充
   列补零兜底。

## 适用场景
- 纯向量 AIV 注意力（QK^T→S→mask→@V），向量管计算饱和（aiv_vec_ratio 高）
- causal / maxAttnLen 窗口用例占比高（全 1 与三角 tile 多）
- 掩码可由索引（colId/rowId/maxAttnLen/causal）静态推导，无需物化 mask 张量

## 实现要点
- **先做掩码来源分析**：把 per-row 掩码循环按"可证明全 1 / 可证明三角 / 需要逐行算"
  三分类，命中前两类走快速路径
- 全 1 路径用 `Muls(x, 1.0f)` 拷贝激活结果，位精确（含 -0.0 保留）
- 三角跳过用 `jMax = min(i+1, kvRows)` 精确剪枝，`0*v=0` 位精确
- S 融合依赖 kvUb 尾行/填充已清零的既成事实，若清零被破坏需补零兜底

## 约束 / Trade-off
- 全 1/三角判定条件必须保守（任一条件不满足回退逐行），误判会导致精度错
- 小 shape（tile 少）受益有限，大 shape（tile 多）收益显著
- 与 X71 互补：X71 是纯向量 AIV 重构 + 同步纪律，X72 是在其上做掩码来源驱动的
  向量指令削减

## 验证方法
- **性能**：在目标设备上对父变体与变体做同一时间窗口的 A/B（正反序至少两轮），
  以绝对时延和配对差值判断，不用跨窗口比值。
- **精度**：跑全量精度用例，逐元素对比参考实现；快路径必须与逐行路径逐 bit/逐元素
  一致（必要时用 fp64 参考确认 maxdiff=0）。
- **容量**：核对 UB/L1/L0C 预算与 `kvRows` 尾行/填充清零，确认无越界或脏读。
