---
type: Optimization
title: 短序列分块参数网格重调（MTP / S∈[2,16] 场景）
description: 将固定分档函数替换为按S档、S_kv档和任务量档索引的参数表。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/02-shortseq-tiling-grid-retune.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：短序列分块参数网格重调（MTP / S∈[2,16] 场景）

> **单一优化点：** 对 S∈[2,16]（MTP）及被 decode 分档连带的小/mid shape，
> 把 mBase/s2Base/headChunk 的**固定分档策略函数替换为按 (S, S_kv, B×N_kv×G)
> 键控的参数表**，用 bench harness 逐格扫描后冻结优胜组合——不引入任何新
> kernel 机制，纯 host tiling 参数重调。

> **已验证锚点：** GQA bench 子集 0.1546→**0.1236ms（-20%，全程单轮最大收益）**，
> score 0.622→0.777。单 case：case16（fp16 MTP B60 S2 Skv2048 causal）447→**200us
> （-55%）**、case3 42→30us、case1 18→14us、case8 330→314us。20/20 allclose。
> 注意：该轮收益在 01/03/05/06 全部落地后的基线上取得——**先做机制、最后做网格**。

---

## 1. 优化原理

### 1.1 性能问题模式

固定分档函数（`s2Base=S<=16?1024:512`、`mBase=S>16?512:按档…`）对 MTP
（S∈[2,16]）与 mid shape 严重失配：

- MTP S=2 走 rowPitch=16 折叠：每头 16 行槽只有 2 有效行（87% 空算），
  且 headChunk=128/16=8 头打包后任务 M 维过小/任务数失衡；
- 小 prefill（S=128/256）复用大 prefill 的 mBase=512，M 维尾块浪费大；
- 分档边界形状（S 恰在档位切换处）波动剧烈。

### 1.2 本策略利用的硬件机制

| 机制 | 利用方式 |
|---|---|
| host tiling 参数表 | 按 (S 档, S_kv 档, 任务量档) 键控 mBase∈{16..512}、s2Base∈{128..1024}、headChunk∈{1..G}、ring 深度∈{1..3}，替换两个固定策略函数 |
| bench 闭环 | 每个键控组合跑子集 bench（kernel 级计时）取均值最优冻结——参数空间人手不可扫（数十组合 × 每组合 8 case） |
| 小 shape 快流水 | 小任务量键位同时收 ring 槽深（3→1）削减 flag 链填充延迟（与被证伪的"全局同步削减"不同：只动小 shape 键位，不伤 decode 大 case） |

### 1.3 核心改动点

- `op_host/gqa_tiling.cpp`：`SelectS2BaseSize/SelectMBaseSize` 两个固定函数 →
  形状键控表（TilingData 结构不变，kernel 侧零改动）。
- MTP 键位：S∈[2,16] 的 headChunk 减小（如 8→2/4）换 headBlocks×s2OuterBlocks
  任务数，配合更小 s2Chunk 提高 8 核占用率与归并并行度。
- 小 prefill 键位：mBase 降到与 S 匹配（尾块浪费 <半块）。

## 2. 正确性红线

- **只改参数不改机制**：任何 (mBase,s2Base,headChunk) 组合都必须过全量 20 case
  allclose——尤其 causal 块格对齐改变后掩码档位判定路径（05 号的块级跳过判定
  依赖块格，需联合回归）。
- 网格扫描期间禁止放宽精度阈值；单格结果必须可复测（±2% 噪声内）。
- workspace 五分区尺寸随 mBase/s2Base 变化，重算 perCoreBytes 与总量上限。

## 3. 泛化条件

- **适用**：任何"固定分档函数 + 多档边界 shape"的算子；bench 子集能代表真实
  负载时收益最可靠（本例 8 case 子集扫描直接优化目标均值）。
- **不适用**：机制级瓶颈（带宽/流水）未解决时——先机制后参数，否则网格结果
  会被后续机制改动作废（本包 04→02 的顺序教训：04 在旧分档上迭代到 0.1544，
  02 一轮重扫直接 0.1236）。
- 目标域外推风险：子集外 case（2/4/5/6/7/9/10/13/17~20）未见回退（全量精度
  通过 + 抽查），但参数表过拟合子集的风险存在——新 shape 域需重扫。

## 4. 实施步骤

1. 把两个固定分档函数替换为键控表（先保留原函数为 default 键位）。
2. 对 bench 子集逐 case 扫描候选组合（自动化：改 tiling→build→bench 一格一脚本）。
3. 冻结每键位优胜组合；跑全量 20 case 精度 + 子集 bench 复测（防噪声假阳性）。
4. 登记参数表与扫描日志（复现依据）。

## 5. LLM 前置问题

- 当前 shape 的 mBase/s2Base 由哪档命中？M 维有效行占比、任务数/核数比多少？
- 该键位的历史扫描是否覆盖（避免重复扫）？参数改动是否触碰 causal 块格对齐？
- 子集外 shape 是否有回退证据？

## 6. 风险与回退

- 回退 = 恢复 default 键位（原固定函数），零代码风险。
- 最大风险是**顺序**：在它之后做任何改变任务粒度/块格的机制策略（01/05 的
  参数面），网格表需重扫——因此本策略必须是采纳配方的最后一步。
- 网格过拟合：域外新 shape 回退时按 §4 只重扫该键位。

## 7. 验收标准

- 精度：全量 20 case allclose（禁放宽）。
- 性能：子集均值相对旧分档 ≥5%（本锚点 -20%）；无单 case >5% 回退。
- 可复现：同参数两次 bench 均值差 <2%。

## 检索卡（短卡）

动作：将固定分档函数替换为按S档、S_kv档和任务量档索引的参数表。
适用：适用于固定分档函数覆盖多个边界shape，且bench子集能代表真实负载的情况。
限制：只调整参数、不改变机制；每组mBase、s2Base、headChunk组合均须通过全量allclose。
范围：S∈[2,16]的MTP及小/mid shape。
检索词：host tiling参数表、mBase、s2Base、headChunk、S档、S_kv档、MTP。
机会：固定分档参数与MTP短序列及mid shape失配。
