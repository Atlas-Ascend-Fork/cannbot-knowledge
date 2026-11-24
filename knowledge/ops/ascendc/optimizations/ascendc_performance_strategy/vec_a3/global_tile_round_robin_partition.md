---
type: Optimization
title: 全局 tile 轮转切分替代 per-core 分段（消除非对齐尾块）
description: 将 per-core 分段后切 tile 改为全局 tile 轮转，把非对齐余量集中到最多一个全局尾块。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-global-tile-round-robin-partition.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：全局 tile 轮转切分替代 per-core 分段（消除非对齐尾块）

> 单一优化点：把 per-core `blockLength` 分段 + 块内切 tile 改为全局 tile 轮转分配，将所有非对齐尾块集中为最多 1 个全局尾块。

## 1. 原理
ceil 除法使每核块的模 tile 余数都变成非对齐尾块（n 个 DataCopyPad 慢路径拷贝）；全局 tile 轮转把全部余数集中为最多 1 个全局尾块，其余 tile 全对齐满块。

- 改动量级：基础策略

## 2. 性能问题模式
- 旧切分为 `blockLength = ceil(total/cores)` + 块内再切 tile → 当 blockLength 非 tile 整数倍时**每核**都产生一个非对齐尾块（DataCopyPad 慢路径）；
- 例：1048576 元素/40 核 → blockLength=26215=3×8192+1639，40 个 1639 尾块；
- MTE 低效搬运（per-core 非对齐尾块 DataCopyPad）。

## 3. 正确性红线
- 尾块只允许出现在最后一个全局 tile；GetBlockNum() 必须等于 host blockDim，否则漏/重 tile；
- 空输入 host 提前返回不启动 kernel。

## 4. 泛化条件
- **适用**：可推广至 flat 多核切分 kernel；tile 粒度固定、tile 数 > 核数的中大 shape 收益明显。
- **不适用**：输出需按核连续分段（如后续跨核归约依赖连续窗口）时不能改轮转；tile ≤ 核数时行为与 per-core 切分一致；tile 数远大于核数（>10x）时轮转与按段切分等价，收益消失。
- **回退面（2026-09-22 新增）**：轮转跨步会破坏 per-core GM 局部性，**小/中 shape 回退 2-5%**，抵消尾块收敛收益；仅当大 shape（tile 数 > 核数、<10× 核数）**占比 ≥50%** 时几何平均才为正。非对齐尾块多的算子是真正受益者（P7 1.60×，15 轮实测 7 有效）。

## 5. 实施步骤
1. tiling 结构 `blockLength` → `totalTiles`。
2. kernel Process 改全局轮转：
   ```cpp
   for (int32_t t = GetBlockIdx(); t < totalTiles; t += GetBlockNum())
       ProcessTile(t * tileLength, min(tileLength, totalLength - t*tileLength));
   ```
3. GlobalTensor 直接覆盖全量（不再 per-core 窗口 SetGlobalBuffer）。

## 6. LLM 前置问题
- 后续算子是否依赖输出按核连续分段（跨核归约窗口）？
- tile 数与核数的关系是否在收益区间（tile 数 > 核数、<10x 核数）？
- host blockDim 是否严格等于 kernel GetBlockNum()？
- 空输入路径是否已有 host 提前返回？

## 7. 验收标准
- build + 精度全过；实测战绩（910B3）：P7[1024×1024 fp32] kernel 4.43 → 4.05us（-8.6%）；cast 路径同幅受益；端到端 geo r1 1.47-1.70 → r2 1.68-1.70（kernel 收益明确、端到端在噪声带内正向）。

## 检索卡（短卡）

动作：将 per-core 分段后切 tile 改为全局 tile 轮转，把非对齐余量集中到最多一个全局尾块。
适用：适用于flat多核切分kernel；tile固定且tile数>核数时，可能减少空闲核与尾部不均。
限制：尾块只能位于最后一个全局 tile；核数须匹配 host blockDim；依赖按核连续窗口时禁用；大 shape 占比<50% 时几何平均大概率净负（小/中 shape 回退 2-5%）
范围：tile 粒度固定的 flat 多核切分 kernel。
检索词：blockLength、totalTiles、全局 tile 轮转、DataCopyPad、GetBlockNum
机会：blockLength 不是 tile 整数倍，导致每核各有一个 DataCopyPad 尾块。
