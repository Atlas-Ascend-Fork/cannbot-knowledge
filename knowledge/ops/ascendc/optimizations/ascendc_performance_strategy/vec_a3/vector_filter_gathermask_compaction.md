---
type: Optimization
title: 向量化索引过滤 + GatherMask 命中压缩（把标量工作量从 O(扫描) 降到 O(命中)）
description: 将负索引修正和范围命中判断改为int32向量链，以GatherMask压缩命中项；命中后的RMW仍用标量。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-vector-filter-gathermask-compaction.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：向量化索引过滤 + GatherMask 命中压缩（把标量工作量从 O(扫描) 降到 O(命中)）

> 单一优化点：对"扫描全部索引、按范围/条件判命中、命中才做标量 RMW"的循环，把**判命中这一步向量化**（int32 向量链：负索引修正 + 范围比较 → mask），再用 **GatherMask** 把命中的目标地址/行号/更新值**压缩成连续 run**，标量只作用在压缩后的命中上。标量工作量从 O(扫描量) 降到 O(命中数)。

本策略适用于任何"大量候选、少数命中、命中要标量处理"的 kernel（scatter / gather / segment 匹配 / 稀疏筛选 / topk 带索引等），与具体算子无关。

---

## 1. 原理

**问题形态**：A2 等芯片无随机写/随机 gather 向量指令，命中后的 RMW 只能标量（~2-18ns/op）。但"判一个索引是否命中"（负索引修正、范围比较）**不需要标量**——int32 向量管 128 lanes/cycle 一条指令处理。

**向量化过滤链**（全部 int32 数组操作，`count = 批内 lane 数`）：
1. 负索引修正（分支无跳转）：`sign = min(max(idx, -1), 0); idx += sign * (-axisSize)`；
2. 相对化 + 范围检查：`rel = idx - segStart`；`valid = (rel == clamp(rel, 0, segRows-1))`（A2 int32 Compare 仅 EQ，用 `clamp` 等价实现）；
3. `Compare` 产出 1bit/元素 mask；
4. `GatherMask(mask)` 把命中的 rel 地址、行号、更新值分别压缩成连续 run，`rsvdCnt` 给出命中数；
5. 标量循环只遍历 `rsvdCnt` 个命中做 RMW（地址连续、值预压缩，无数据依赖 UB gather）。

**收益模型**：扫描 524K 索引（纯向量 ~10us）而命中仅 22K；若全标量判命中则 524K × 标量 ≈ ms 级。**判命中向量化把扫描开销压掉 10-100×，标量只付命中成本。**

## 2. 性能问题模式

满足以下模式时考虑本策略：

1. 主循环逐元素：`读索引 → 标量判命中（负索引/范围比较）→ 命中才 RMW`，**每个元素都付标量判命中的成本**。
2. profiling：SCALAR pipe 占比高（>30%），但计算本身只是"比较 + 命中 RMW"，没有复杂算术——说明标量花在了"判定"而非"计算"上。
3. 命中率低（扫描量大、命中量小）或命中稀疏；`GetValue`/标量比较逐元素出现在热点循环。
4. 已按输出切分/条带切分，但每段的"命中判定"仍逐元素标量。

不适用：命中率接近 100%（压缩无收益、反而加向量开销）；无索引/无命中判定的连续搬运或纯 elementwise；int64 数据无 GatherMask 支持（需先 Cast，见 35）。

## 3. 正确性红线

- **mask 与值一一对应**：GatherMask 的 mask 位必须与"更新值/行号"同一 lane 序；若索引与更新值 staging 行步长不同，同一 mask 位对不到对应更新元素——**此时不得用同一 mask 压更新值**，回退到标量按行号 gather。
- **padding lane 必须毒化**：向量链读到批尾 padding（DataCopyPad 填充尾/对齐缝隙）时，padding lane 的 mask 必须保证为 0——用 `INT32_MIN` 毒化 padding 索引，使 `clamp` 后不命中；不毒化会压进脏数据。
- **重复索引语义**：GatherMask 压缩是稳定压缩（保持源序），重复 target 的"后写覆盖 / 累加"顺序必须与标量循环一致；压缩后同一 rel 出现多次时，归约模式要在组内处理（可先做 28 比较组内重复探测选快/慢路径）。
- **int32 Compare 仅 EQ**：范围检查不能直接用 LT/GT，须用 `rel == clamp(rel, lo, hi)` 等价；`Select` 若仅 half/float，负索引修正用 `sign = min(max(idx,-1),0); idx += sign*(-axis)` 分支无跳转实现。
- **向量→标量同步**：GatherMask 产出的压缩结果（rsvdCnt + 压缩数组）被标量读前须 `SyncVectorToScalar`（或对应事件），否则读到未完成数据。

## 4. 泛化条件

适用（任一）：
- 逐元素"判命中"是标量热点，命中率低/稀疏；
- 已向量化批搬索引，但命中判定仍标量；
- 有 `GatherMask`/`Compare` 可用的 dtype（int32/16；int64 需先 Cast）。

不适用（任一）：
- 命中率 ~100%（压缩无收益）；
- 无索引/命中语义的规整算子；
- dtype 无 GatherMask 且不可 Cast（残留 int64 走标量路径）。

## 5. 实施步骤

1. 确认热点是"逐元素标量判命中"（读代码 + SCALAR pipe 占比）。
2. 把判命中链改写为 int32 向量链（负索引修正、`rel==clamp` 范围比较），`Compare` 产 mask。
3. 毒化批尾 padding lane（`INT32_MIN`），保证 padding mask=0。
4. `GatherMask` 分别压缩 rel 地址、行号、更新值（注意更新值仅当索引/更新 staging 步长一致时才可同 mask 压）。
5. `SyncVectorToScalar` 后，标量只遍历 `rsvdCnt` 命中做 RMW。
6. 处理重复索引（组内重复探测）、int64 无 GatherMask（回退标量 gather）等边界。
7. 全量编译、精度全过、多次取样性能。

## 6. LLM 前置问题

- 热点是"判命中"标量还是"命中 RMW"标量？命中率多少？
- 索引/更新值的 staging 行步长是否一致（决定能否共用 mask）？
- 批尾 padding 是否毒化？重复索引的"后写/累加"顺序是否保持？

## 7. 验收标准

- 精度：全量用例通过（含 padding 毒化、重复索引、负索引、int64 回退路径）。
- 性能：SCALAR pipe 占比显著下降，命中判定改向量后扫描开销压掉 10-100×（scatter 案例配合 32 把 case1 从 11ms 压到 <500us 量级）。
- 结构：主循环命中判定无逐元素标量比较。

## 检索卡（短卡）

动作：将负索引修正和范围命中判断改为int32向量链，以GatherMask压缩命中项；命中后的RMW仍用标量。
适用：逐元素命中判断是标量热点且命中稀疏，或索引搬运已向量化但判断仍为标量。
限制：GatherMask的mask位必须与更新值或行号保持同一lane顺序。
范围：全索引扫描中的条件过滤、命中压缩及后续标量RMW。
检索词：GatherMask、Compare、int32向量链、负索引修正、范围比较、命中压缩、标量RMW
机会：主循环逐元素读取索引、标量判命中，只有命中时才执行RMW。
代价：缺少随机写或随机gather向量指令时，命中后的RMW无法向量化。
