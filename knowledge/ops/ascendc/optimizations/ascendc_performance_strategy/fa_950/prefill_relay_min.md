---
type: Optimization
title: prefill GM 中转最小化（P/O 中转字节削减，两轮迭代）
description: 保留 GM 五分区中转架构，按有效行列缩减 MM1→Vec1→MM2→Vec2 的 GM 往返字节。
tags:
- task.optimization
- topic.attention
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/04-prefill-relay-min.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：prefill GM 中转最小化（P/O 中转字节削减，两轮迭代）

> **单一优化点：** 在不改变"GM 五分区中转"架构的前提下，逐项削减 prefill
> 路径上 MM1→Vec1→MM2→Vec2 之间的 GM 往返**字节数**：P/O 区写读粒度收紧、
  尾块不写 padding、无效行不落盘（`fixParams.mSize=有效值` 四处统一口径）。

> **已验证锚点：** GQA bench 子集 0.1632→0.1575ms（第一轮 fam_prefill_relay_min）
> →**0.1544ms**（第二轮迭代 _i00），合计 -5.4%；case8 388→约 330us。20/20 allclose。
> 注意：同机制的早轮尝试（fam_relay_min，0.1632 持平无增益）证明**该策略收益
> 依赖前置策略就位**（03 的 wsS 2B + 05 的块跳过先行），属压榨尾巴型。

---

## 1. 优化原理

### 1.1 性能问题模式

五分区中转的隐性别浪费：

- Fixpipe `mSize` 用对齐宽（mRowsAlign）而非有效行：尾块把 padding 行也写 GM；
- P 区写读按整槽（s2Base 宽）而非 kvRows 有效列：OOB 列白搬；
- O 区（fp32 mBase×dim）在 D=256 时双段各写 padding 列；
- 环形槽切换时上一槽残留区的无效读写。

单看每项 <5% 流量，prefill 大 case（case8/10）叠加达 10%+。

### 1.2 本策略利用的硬件机制

| 机制 | 利用方式 |
|---|---|
| Fixpipe 有效值口径 | `fixParams.mSize=mRows`（尾块不写 padding 行）`nSize` 统一有效列宽四处（装载/Mmad/Fixpipe）一致，OOB 列由 Vec1 掩码/oriSrcK 排除 |
| DataCopy 粒度 | P/O 区读写按 kvRows/qRows 有效行列；Vec2 归一只处理有效行（行界钳制后仅有效行过 VF5） |
| 字节宽度 | P 区维持 2B（QType）+ O 区 fp32 不动——本策略不动 dtype（那是 03/07 的地盘），只动"搬多少" |

### 1.3 核心改动点（两轮迭代的差异）

- 第一轮：Fixpipe mSize/nSize 全位点改有效值；Vec2 mChunk 行界钳制。
- 第二轮（_i00）：P 区尾列（kvRows 非整块）写读收边 + O 区 D=256 双段
  padding 列收边；环形槽残留读消除。

## 2. 正确性红线

- 有效值口径必须**四处统一**（装载/Mmad mp.n/Fixpipe nSize/读回侧），任何
  一处仍用对齐宽会产生行列错位（表现：首 case 即精度崩）。
- OOB 列排除依赖 Vec1 的 `oriSrcK=kvRows`（SoftmaxFlashV2 源形状）与掩码链，
  收边后必须重验 causal 尾块列（05 号块格边界）。
- online rescale 累加序不变（wsAccO prev/cur 槽次序与读序），只动宽度不动序。

## 3. 泛化条件

- **适用**：任何 GM 中转架构的"尾块/对齐宽/padding"浪费——收益与 shape 尾部
  失配度成正比（D=256 双段、S/S_kv 非整块最肥）。
- **不适用**：中转区本身可消除的场景（→09 号 p_direct_mm2 才是根治）；带宽
  占比已被 03 号压缩到 <20% 后收益趋零（本包第三轮迭代实测持平）。

## 4. 实施步骤

1. 盘点五分区每个写/读位点的宽度公式，标出"对齐宽 vs 有效值"差集。
2. 逐位点改有效值（保持四处统一不变量），每改一处跑全量精度。
3. profiler 旁证：MM1/Vec1/MM2/Vec2 的 GM 读写字节下降。
4. 两轮迭代：先行列有效值，再尾块收边。

## 5. LLM 前置问题

- 每个中转区写读位点的宽度公式是什么（对齐宽 or 有效值）？
- 尾块占比多少（S/S_kv/D 对块基取余的余量）？
- 有效值改动是否与 causal 块格判定（05）和 wsS 宽度（03/07）耦合？

## 6. 风险与回退

- 回退 = 恢复对齐宽公式（纯参数面，零机制风险）。
- 四处统一被破坏时首 case 即崩（快速失败，好定位）；慢性风险是 OOB 列排除
  失效导致的隐蔽精度损失——必须跑 cann-bench 小值域口径。

## 7. 验收标准

- 精度：20 case allclose + sequential 场景（行界钳制易暴露跨调用残留）。
- 性能：prefill 大 case 累计 ≥5%；decode 噪声内。
- 字节旁证：中转区总读写字节下降 ≥10%。

## 检索卡（短卡）

动作：保留 GM 五分区中转架构，按有效行列缩减 MM1→Vec1→MM2→Vec2 的 GM 往返字节。
适用：GM 中转架构存在尾块、对齐宽或 padding 导致的无效搬运。
限制：装载、Mmad mp.n、Fixpipe nSize 与读回侧的有效值口径必须统一。
范围：prefill 的 MM1→Vec1→MM2→Vec2 中转路径
检索词：prefill、GM 五分区中转、Fixpipe、mSize、mRows、padding、有效列宽
机会：尾块仍写 padding 行，或中转区按整槽宽度读写。
代价：适用价值随 shape 尾部失配度变化。
