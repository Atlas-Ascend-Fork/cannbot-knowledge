---
type: Optimization
title: causal 整块全掩码跳过（块级稀疏计算删除）
description: 用整数边界判定并跳过causal下整块全掩的s2块，删除对应块级计算。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/05-causal-block-skip.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：causal 整块全掩码跳过（块级稀疏计算删除）

> **单一优化点：** is_causal 时，对"整块落在掩码区"的 s2 块（块内全部列
> `j > i_max + (S_kv−S)`，即对任务内所有 query 行都不可见）在任务创建层直接
> 跳过 MM1/Vec1/MM2/Vec2 全链路——不装载、不计算、不落盘、不发 flag。

> **已验证锚点：** GQA bench 子集 0.1676→0.1632ms；case8（fp16 B4 S1024
> Skv1024 causal）388→359us（**-7.5%**）、case10/16 同向受益。20/20 allclose。
> 块格捕获率理论 (T-1)/2T（T=⌈S/128⌉，S=1024 时约 49%），实测节省 7.5%
> ——跳过的是 Vec1/MM2 的部分流量与 MM1 尾部，K 装载等固定开销仍在。

---

## 1. 优化原理

### 1.1 性能问题模式

causal 右下角对齐掩码（`j > i + (S_kv−S)` 置 -inf）下，任务内**靠后的 s2 块
整块全掩**：qRowStart 越靠 S 尾部，全掩块越多（对角线以上的 KV 块）。基线
对这些块仍执行完整 MM1→softmax(全 -inf 行)→MM2(P=0 贡献)→rescale(×1) 链路。

### 1.2 本策略利用的硬件机制

| 机制 | 利用方式 |
|---|---|
| 块级判定 | 全掩条件是 tiling 标量 + 游标的**纯整型函数**：`s2Start ≥ colLimit = S_kv − S + (qRowStart + qRows − 1) + 1`（任务最末 query 行都看不到的块）；AIC 与双 AIV 在同一循环各自算出同一结果（禁 coreIdx/运行期状态），三核任务序列逐位一致 |
| 删除恒等性 | 全掩块对 online softmax 状态环是 m 不变、sum×1；P=0、MM2 贡献 0、Vec2 rescale 因子 1 —— 删除后数值逐位恒等（不需重新归并证明） |
| 跳过语义 | CreateTask 三态返回 `kCreated/kSkipS2/kSkipTask`：kSkipS2 不写 runInfo、不占 ring slot、不发任何 flag，调用方仅推进游标 |

### 1.3 核心改动点

- `op_kernel/gqa_kernel.h`：CreateTask 返回三态枚举；主循环对 kSkipS2 仅
  AdvanceTaskCursor（createdTaskCount/executedLoop 不进位——ring slot 序与
  loop%3 解耦点必须重验）。
- host `gqa_tiling.cpp`：causal 长 prefill 细分块档（仅 S>128 时全掩块才可能
  落在块格点上；S<=128 qOuterBlocks=1 无收益且扰动现网，保持原策略）——
  块格捕获率与 mBase 联动，**05 与 02 的块格参数面耦合**。
- flag 配平：跳过块不发 P_READY/O_READY，消费侧 Wait 按 slot 交替序列对齐
  （全掩块不进 slot 序，时序证明依赖"三核同一判定"）。

## 2. 正确性红线

- **三核判定一致性**是生死线：判定只能依赖 tiling 标量与游标（禁 coreIdx/
  subBlockIdx/运行期状态），否则 AIC 与 AIV 的 slot 序错位 → 死锁或数据错配。
- 删除恒等性依赖"全掩行 softmax 输出对状态环中性"（m 不变、sum×1）——若后续
  策略改变 state 更新语义（如 sum 乘 exp 因子的实现方式），必须重证。
- colLimit 边界：`j > i + (S_kv−S)` 是右下角对齐；S==S_kv 退化为标准下三角，
  块格判定在两语义下同式（用统一公式，勿按 S==S_kv 特判）。

## 3. 泛化条件

- **适用**：任何因果/带状掩码 + 分块计算的组合；捕获率随 S/块基增大上升
  （S=1024/块 128 约 49%）。MTP/decode（S<=16）通常 qOuterBlocks=1 无整块可跳。
- **不适用**：非 causal；掩码边界不与块格对齐时只能块内掩码（档2 maskDiff），
  块级跳过仅消化"整块全掩"部分。

## 4. 实施步骤

1. host 推导 colLimit 并入 TilingData 标量（或 kernel 侧由现有标量推导，零新字段）。
2. CreateTask 三态化 + 主循环 kSkipS2 分支（游标推进不进 slot）。
3. 全量精度（重点 causal case 1/3/5/6/8/10/16/17/19/20）+ sequential 场景
   （跳过块的跨调用 slot 残留最易在此暴露）。
4. 与 02 号联合：块基参数改变后捕获率变化，网格重扫时把跳过块数纳入模型。

## 5. LLM 前置问题

- 掩码语义是右下角对齐还是标准下三角？块格（mBase/s2Base）下整块全掩的
  块数/总块数比例？
- 跳过判定可否写成纯（tiling 标量, 游标）整型函数（三核一致前提）？
- ring slot 序与 loop 序的耦合点在哪（跳过块不占 slot 后是否仍闭合）？

## 6. 风险与回退

- 回退：判定函数恒返回 kCreated 即整支关闭，零残留。
- 最大风险是三核不一致（死锁表现：偶发卡死在 Wait）——sequential 场景 +
  多次重复跑是必须的验收项。
- 收益预期管理：捕获率 ≠ 时延节省比例（K 装载固定开销仍在），按实测 1/6 的
  捕获率→时延折算预期。

## 7. 验收标准

- 精度：20 case allclose（causal 全集）+ sequential 双场景 × 重复 3 次。
- 性能：causal 长 prefill ≥5%（本锚点 case8 -7.5%）；非 causal 零回退。
- 旁证：profiler 中该任务的总 Mmad/Vec 指令数下降与捕获块数一致。

## 检索卡（短卡）

动作：用整数边界判定并跳过causal下整块全掩的s2块，删除对应块级计算。
适用：适用于因果或带状掩码的分块计算；单个q外块且无整块可跳时不适用。
限制：三核判定必须一致，且只能依赖tiling标量与游标，禁止依赖核索引或运行期状态。
范围：is_causal路径中的分块s2计算。
检索词：causal右下角掩码、全掩s2块、块级判定、colLimit。
机会：任务靠后的s2块存在整块全掩。
