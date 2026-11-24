---
type: Optimization
title: 精确 UB tiling（仅调每批行数 + bf16 批量 Cast，不重构主循环）
description: 纳入全部片上缓冲精确反算每批行数，并将bf16逐行Cast改为批量Cast；不重构主循环
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/precise-ub-tiling-only.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：精确 UB tiling（仅调每批行数 + bf16 批量 Cast，不重构主循环）

单一优化点：精确 UB tiling + bf16 批量 Cast（不重构主循环）。针对「UB 预算粗放、每批行数被固定小上限钉死、bf16 逐行 Cast」——把 softmax/topk 等段的内部临时 buffer 全部纳入 UB 预算精确反算每批行数（去掉固定小上限），按末维动态放大批量；bf16 路径用跨行向量化批量 Cast 替代逐行标量 Cast。**显式约束：只改每批行数与 Cast 方式，不重排主循环、不引入软件流水 / 手动 HardEvent 同步**（主循环保持原 搬入→计算→搬出 串行 + 框架默认 double-buffer 即可）。

## 1. 原理
- **UB 预算粗放**：若只按「输入+输出 buffer」估每批行数，忽略 softmax/topk 内部临时区，会硬设小上限（如固定 32 行），导致小末维时明明能装几百行却只装几十行，搬运粒度碎。
- **精确 tiling**：每批行数 = floor((UB 预算 − 各段临时区总和) / (每行常驻 buffer × buffer 数))，UB 预算用满（约 75%，留余量给 topk scratch），按末维动态，小末维允许大行数；rowsPerUb 上限取末维对齐值（避免框架高阶 API 在大 rowsPerUb 下 tiling 低效）。
- **单核退化防护**：向上对齐 rowsPerCore 使 (核数-1)×rowsPerCore > 总行数时，重算 floor(总行数/(核数-1)/rowsPerUb)×rowsPerUb，保证多核并行（小总行数 + 大 rowsPerUb 场景）。
- **bf16 批量 Cast**：bf16→float 用跨行向量化（带末维对齐 stride）一次性 Cast 整批，替代逐行标量循环。
- **tile 极限化削减标量循环开销**：每 tile 的 AllocTensor/EnQue/DeQue/FreeTensor 与循环控制走 scalar/控制路径（msprof 的 aiv_scalar_ratio 直接反映其占比）；tile 增大 k% → 迭代数降 k/(1+k)，scalar 部分等比缩小。对已处带宽/算力屋顶的 case 零收益但也零退化（免费 knobs）。

## 2. 性能问题模式
- 每批行数被固定小上限（如 32）钉死，或预算只算输入输出不算临时区；小末维 case 尤其吃亏。
- bf16 逐行 Cast 浪费向量带宽。

## 3. 正确性红线
- **UB 容量**：精确反算后须留余量，禁止越界；各段临时区（softmax max/sum、topk scratch、cast 中转）都要计入。
- **rowsPerUb 上限用末维对齐值**（非完全去掉）；fallback 重算须保多核。
- **bf16 批量 Cast** 的 stride/对齐须匹配 buffer 布局。
- **不要动主循环结构 / 同步**（避免引入数据竞争；软件流水是另一个独立策略，本策略不涉及）。

## 4. 泛化条件
- **适用**：UB 预算估算粗放、每批行数被固定小上限的算子；bf16 逐行 Cast 的算子。
- **不适用**：UB 已精确的算子；主循环串行已是瓶颈、需要软件流水化的算子（用专门的软件流水策略）。
- **屋顶预检（2026-09-22 新增，选路阶段执行）**：先采集 op_summary 流水占比；当 `mte_ratio≥0.9` 且实测带宽已 >1TB/s（算子已达 mte/vec 带宽屋顶）时**零收益**——标量开销下降但总时长不动，直接不选。

## 5. 实施步骤
1. 列出所有 on-chip buffer（输入/输出/各段临时区/cast buf），精确计算每批行数上限（按末维动态，UB 约 75%），rowsPerUb 上限 = 末维对齐值。双缓冲队列形态的通用预算公式：`in×B + out×B + work×N ≤ UB`（B=缓冲份数，N=工作区份数），tile 长度取该预算极限。
2. rowsPerCore fallback 防 small-totalRows 单核退化。
3. bf16 路径启用跨行向量化批量 Cast（替代逐行）。
4. **保持主循环原结构**（不引入 preload / 软件流水 / HardEvent 重排）。
5. build + 精度全过 + latency 下降（尤其小末维 case）；已在 mte2/vec 屋顶的 case 允许零变化（负结果如实标注）。

## 6. LLM 前置问题
- 每批行数当前怎么算？忽略哪些临时区？固定小上限是多少？
- bf16 Cast 是逐行还是批量？跨行 stride 怎么算？
- 主循环结构是什么？（本策略不改它，只改 tiling 计算 + Cast）

## 7. 验收标准
- build + 精度全过；延迟下降（尤其小末维 case）；主循环结构不变。
- tile 极限化补充实测（910B3，3-rep 一致）：非饱和 case 各 -0.7~1%，总 geo 稳定带 1.18-1.31 → 1.27-1.31，无退化；带宽屋顶 case（64M fp32）零变化（负结果如实标注）。

## 检索卡（短卡）

动作：纳入全部片上缓冲精确反算每批行数，并将bf16逐行Cast改为批量Cast；不重构主循环
适用：UB预算粗放、每批行数受固定小上限约束，或存在bf16逐行Cast
限制：UB反算必须留余量且不得越界；mte_ratio≥0.9 且带宽>1TB/s 的屋顶 case 零收益，选路先采 op_summary
范围：softmax/topk片上批处理与bf16 Cast
检索词：精确UB tiling、rowsPerUb、softmax临时区、topk scratch、批量Cast
机会：固定小批量、预算遗漏临时区，或bf16仍逐行Cast
代价：不适用于需靠软件流水解决主循环串行瓶颈的算子
