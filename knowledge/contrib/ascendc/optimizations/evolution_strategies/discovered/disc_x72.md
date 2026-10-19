---
type: Optimization
title: "掩码来源分析削减向量管计算（全 1 快路径 + 对角三角跳过 + S 广播融合）"
description: "纯向量 AIV 注意力（Cube 不可用）的瓶颈是向量管计算饱和（aiv_vec_ratio≈0.83）。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.reduction
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# X72: 掩码来源分析削减向量管计算

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> schema_version: okf.v1
> kind: discovered_strategy
> id: X72
> title: "掩码来源分析削减向量管计算（全 1 快路径 + 对角三角跳过 + S 广播融合）"
> origin: discovered
> discovered_round: 3
> discovered_from: "103_HSTU evolution, round_3/parallel_2 (x0_x1_x1, open_exploration)"
> base_speedup: "3.99x → 4.57x geomean vs PyTorch（+14.5%；大 case 普遍 1-77% 提升，50/50 精度 PASS，fp64 maxdiff=0）"
> confidence: single_op
> status: active
> op_families: [attention, flash_attention, mha, gqa]
> bottlenecks: [compute_bound, partial_overlap]
> tags: [mask-provenance, full-mask-fastpath, diagonal-triangular-skip, s-broadcast-fusion, vector-pipe-reduction, bit-exact, 910b2c]
> strategy_ids: [X71, P94, P123]
> ```

## 核心思路
纯向量 AIV 注意力（Cube 不可用）的瓶颈是向量管计算饱和（aiv_vec_ratio≈0.83）。
对**掩码的来源做静态分析**，识别"掩码可证明为全 1 / 三角"的 tile，直接跳过对应
向量计算；同时对 S 广播/归约做融合削减。三项技术全部位精确（`x·1.0=x`）：

1. **全 1 掩码快路径**（ComputeV1）：当 tile 掩码恒为 1（无 mlen 窗口、整 tile
   全历史列 `col < n-nt`、非因果或因果下非对角线 `t<qbLocal`、非尾块 `kvRows=64`）
   时，跳过整个 per-row 掩码循环（~31 向量指令 + 1 GetValue/行），仅用单条
   `Muls(sUb, kvUb, 1.0f)` 拷贝。大 case 约 6/8 tile 命中。
2. **对角 tile PV 三角跳过**（ComputePV）：因果且无 ctx/mlen 的对角线 tile
   （`t==qbLocal`）掩码为三角（`j<=i`），跳过 `j>i` 的 Axpy（`0*v=0` 位精确），
   省对角线 tile 一半 PV。
3. **S 广播+乘融合**（ComputeS）：父代 `2-pass`（64 次 Adds 广播 + 1 次整块 Mul）
   改为单次 per-(i,j) `Mul(red[j], qRow, kvUb[j])`，S 向量指令减半（8192→4096），
   并消掉 Adds→Mul 的 PIPE_V 屏障（每 tile 省 64 条）。kvUb 尾行/填充已清零 → 尾
   j 行 `red=qRow*0=0`、ReduceSum 尾列恒 0，精度不变；D 非 16B 对齐时对 red 填充
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
- 精度验证必须全量 50 case + fp64 参考逐元素 maxdiff=0（位精确）

## 约束 / Trade-off
- 全 1/三角判定条件必须保守（任一条件不满足回退逐行），误判会导致精度错
- 小 case（L<600）受益有限（tile 少），大 case（L≥2000）收益显著
- 与 X71 互补：X71 是纯向量 AIV 重构 + 同步纪律，X72 是在其上做掩码来源驱动的
  向量指令削减

## 来源
自动发现于第 3 轮进化，算子 103_HSTU（open_exploration x0_x1_x1），speedup 3.99x→4.57x geomean
