---
type: Optimization
title: slot 环形分级软流水（MM1/Vec1/MM2/Vec2 交错重叠）
description: 将 3 个环形 workspace 槽改为分级软流水，使相邻槽分别处于 MM1、Vec1/MM2、Vec2
tags:
- task.optimization
- topic.attention
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/06-staged-ring-pipeline.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：slot 环形分级软流水（MM1/Vec1/MM2/Vec2 交错重叠）

> **单一优化点：** 把 RING_SLOTS=3 环形 workspace 槽真正用成**软流水深度**——
> 任务循环按"装 K/V(slot n+2) → MM1(slot n) → Vec1(slot n) → MM2(slot n−1) →
> Vec2(slot n−2)"的相位交错推进，相邻任务的 MTE 搬运与前一任务的 Cube/Vector
> 计算重叠，消除逐任务串行的"搬运-计算-搬运"空泡。

> **已验证锚点：** GQA bench 子集 0.1652→0.1631ms（-1.3%），全局各 case 均衡
> 小幅改善。20/20 allclose。收益克制的原因：基线已有 slot 环形结构（含
> PRELAUNCH=2 预发），本策略是把预发深度与相位真正拉满，属压榨型。

---

## 1. 优化原理

### 1.1 性能问题模式

三段中转架构下任务天然串行段：MM1(装 K/V→Mmad→Fixpipe 落 wsS) → Vec1(取
wsS→softmax→落 wsP) → MM2(取 wsP→Mmad→落 wsO) → Vec2(取 wsO→rescale→写 y)。
每段内部 MTE 与 V/A 计算若不与**相邻任务**重叠，每任务白付搬运空泡
（大 prefill 任务 mBase=512 时空泡占比 ~10-20%）。

### 1.2 本策略利用的硬件机制

| 机制 | 利用方式 |
|---|---|
| 环形槽相位 | 3 slot 各处不同阶段：slot n 在 MM1 时，slot n−1 在 Vec1/MM2、slot n−2 在 Vec2——flag 按 slot 严格交替（Set/Wait 序列闭合） |
| MTE 预发 | K/V 装载提前 2 个任务发起（GQA_PRELAUNCH=2）：第 n+2 任务的 Nd2Nz 装载与第 n 任务计算完全隐藏 |
| 队列双缓冲 | L1/L0 队列 depth 2（vQueL1/kpQueL1/queL0A/B），装载与消费按队列异步 |
| in-order 语义 | 同 PIPE 内指令保序 + CrossCoreFlag 跨核同步——相位推进只需 loop 级游标，无新增 flag |

### 1.3 核心改动点

- 主循环相位重排：装载游标与计算游标分离（lead=2），按 slot 相位分派四阶段。
- PRELAUNCH 深度与 RING_SLOTS 绑定核验（3 槽支持 lead≤2；加深需扩槽 →
  workspace 与 state 缓存同比增）。
- Vec2 的 rescale 读 prevSlot 的 wsAccO 与 state（expCache/maxCache/sumCache
  按 slot×stateStride 索引已就位，本策略零 state 结构改动）。

## 2. 正确性红线

- **flag 配平不变式**：每 slot 的 Set/Wait 交替序列在跳过块（05 号 kSkipS2
  不占 slot）与空行配平（Vec1 空行仍 Set）下必须闭合——相位重排不新增 flag，
  但消费序改变后需全组合回归。
- online rescale 的 prev/cur 槽次序：Vec2 读 prevSlot wsAccO 必须是"该任务
  上一 s2 块"的槽（相位交错后 slot 归属游标推导需重验，KP-011 坐标系单点口径）。
- run-to-run 确定性：相位重排不引入竞争（in-order + flag 已保证），但需
  sequential 场景多次重复验证无偶发错配。

## 3. 泛化条件

- **适用**：任何"多阶段 + 环形槽中转"的任务循环；任务数 >> 槽数（流水可填满）。
  大 prefill（任务大、段间空泡绝对值大）收益最明显。
- **不适用**：任务数 < 2×槽数（流水填充/排空占比高，可能负收益）；阶段间
  数据依赖必须跨槽传递且槽结构尚未存在的架构（需先落环形中转基建）。

## 4. 实施步骤

1. 确认环形槽与 state 缓存的 slot 索引闭合（基线若只有结构没有相位，先补
   PRELAUNCH 游标分离）。
2. 按 lead=2 重排主循环四阶段分派；每任务循环不变量（游标推进/slot 占用/
   flag 配平）加断言式注释。
3. 全量精度 + sequential × 3；profiler timeline 旁证：MTE 与 V/A 时间轴重叠。

## 5. LLM 前置问题

- 当前主循环是逐任务串行还是已有部分预发？段间空泡在哪段最大（timeline）？
- RING_SLOTS 与 PRELAUNCH 深度的关系？加深槽数的 workspace/state 代价？
- 跳过块（若有块级稀疏）在相位流水中的 slot 归属如何闭合？

## 6. 风险与回退

- 回退：lead 置 0 即回逐任务串行（相位是纯调度面）。
- 最大风险是 slot 归属推导错（表现：偶发精度错或卡死）——坐标单点口径
  （totalGSq/s2Cur/loop%3 三者不混写）是防线。
- 收益预期：结构已半就位时 1~2% 量级（本锚点）；从零建相位可到 5-10%。

## 7. 验收标准

- 精度：20 case allclose + sequential × 3 次。
- 性能：全局子集 ≥1%（本锚点 -1.3%）；无单 case >3% 回退。
- timeline 旁证：MTE 空泡时间轴明显收窄。

## 检索卡（短卡）

动作：将 3 个环形 workspace 槽改为分级软流水，使相邻槽分别处于 MM1、Vec1/MM2、Vec2
适用：多阶段环形槽中转循环，且任务数远大于槽数
限制：各slot的Set/Wait须交替配平；环形槽与state缓存的slot索引闭合，并按lead=2分派。
范围：多阶段环形 workspace 槽任务循环
检索词：RING_SLOTS=3、slot 相位、MM1、Vec1、MM2、Vec2、workspace
机会：MM1、Vec1、MM2 经 workspace 中转而天然串行
