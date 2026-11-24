---
type: Optimization
title: 精确 UB tiling + 软件流水（搬运/计算/写出重叠）
description: 纳入全部片上缓冲动态反算批量并移除固定小上限，同时重排主循环以重叠搬运、计算和写出
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/precise-ub-tiling-pipeline.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：精确 UB tiling + 软件流水（搬运/计算/写出重叠）

单一优化点（针对「双 buffer 形同虚设、循环严格串行、UB 预算粗放」）：把 softmax/topk 等段的内部临时 buffer 纳入 UB 预算精确反算每批行数（去掉固定小上限），并重排主循环为 preload + (Compute(i) ∥ CopyIn(i+1) ∥ CopyOut(i)) 的软件流水，让 MTE2/V/MTE3 真正重叠。

## 1. 原理

两个耦合问题：
- **UB 预算粗放**：若只按「输入+输出 buffer」估每批行数，忽略 softmax/topk 内部临时区，会低估或硬设小上限（如固定 32 行），导致小末维时明明能装几百行却只装几十行，搬运粒度碎、流水跑不起来。
- **循环串行**：双 buffer 分配了但主循环仍 CopyIn→Compute→CopyOut 严格串行，加大量化的全屏障，MTE2（搬入）/V（计算）/MTE3（搬出）三段完全不重叠，吞吐减半甚至更低。

精确 tiling：每批行数 = floor((UB 预算 − 各段临时区总和) / (每行常驻 buffer × buffer 数))，按末维动态，小末维允许大行数。
软件流水：preload 块0 → for i: Compute(i) 与 CopyIn(i+1) 与 CopyOut(i-1) 并发（靠细粒度 HardEvent 同步而非全屏障）→ 收尾。

## 2. 性能问题模式

- 现状：每批行数被固定小上限（如 32）钉死，或预算只算输入输出不算临时区；主循环串行 + 全屏障。
- 小末维 case 尤其吃亏（本可大批量却被迫小批量）。
- 即使有 double buffer，延迟仍被串行三段限制。

## 3. 正确性红线

- **UB 容量**：精确反算后须留余量，禁止越界；各段临时区（softmax max/sum、topk scratch、cast 中转等）都要计入。
- **流水同步**：用细粒度 HardEvent（MTE2→V、V→MTE3、V→S 等）替代全屏障；事件 ID 复用须正确，避免死锁/竞态。
- **边界**：preload/收尾段、最后一批的行数（tail）须单独处理；流水深度与 buffer 数匹配。
- **double buffer**：buffer 数 ≥ 2 才能做段间重叠；Compute 与 CopyIn/CopyOut 访问不同 buffer 槽（逻辑序号取模）。

## 4. 泛化条件

- **适用**：主循环含搬入+计算+搬出三段、且有 double buffer 但未重叠的算子；UB 预算估算粗放的算子。
- **不适用**：单段算子（无搬入/搬出可重叠）；UB 已精确且已流水化的算子。
- **屋顶预检（2026-09-22 新增，选路阶段执行）**：先采集 op_summary 流水占比；当 `mte_ratio≥0.9` 且实测带宽已 >1TB/s（算子已达 mte/vec 带宽屋顶）时**零收益**——改 tile 只移动末波相位，不改变墙钟，直接不选。

## 5. 实施步骤

1. 列出所有 on-chip buffer（输入/输出/临时区），精确计算每批行数上限（按末维动态，去掉固定小 cap）。
2. 主循环重排：preload 首块 → 循环内 Compute(i) + CopyIn(i+1) + CopyOut(i-1)（按 buffer 槽取模）→ 收尾 Compute/CopyOut。
3. 全屏障 → 细粒度 HardEvent（按依赖方向设/等 flag）。
4. 验证 tail、事件 ID、buffer 槽不冲突。

## 6. LLM 前置问题

- 每批行数当前怎么算？是否忽略 softmax/topk 临时区？是否有固定小上限？
- 主循环是否串行？有几段？是否用全屏障？buffer 数是多少？
- 哪些段可重叠（MTE2/V/MTE3）？

## 7. 验收标准

- build + 精度全过；延迟下降（尤其小末维 case）；流水使三段重叠。

## 检索卡（短卡）

动作：纳入全部片上缓冲动态反算批量并移除固定小上限，同时重排主循环以重叠搬运、计算和写出
适用：主循环含搬入、计算、搬出，已有双缓冲但未重叠，或UB预算粗放
限制：UB反算必须留余量且不得越界；mte_ratio≥0.9 且带宽>1TB/s 的屋顶 case 零收益，选路先采 op_summary
范围：含搬入、计算、搬出的主循环
检索词：精确UB tiling、double buffer、软件流水、preload、softmax/topk临时区
机会：主循环仍串行并使用全屏障，双缓冲未形成重叠
代价：单段算子无可重叠的搬入或搬出，不适用
