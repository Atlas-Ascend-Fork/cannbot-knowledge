---
type: Optimization
title: 因果掩码 visEnd 归约块裁剪 + 块内列宽自适应
description: 为每个Q块计算保守联合可见终点visEnd，停止为整块不可见的s2后缀生成任务。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/01-causal-visend-reduce-tile-pruning.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：因果掩码 visEnd 归约块裁剪 + 块内列宽自适应

> **单一优化点：** kernel 任务生成阶段按因果掩码为每个 Q 块推导保守联合可见终点
> `visEnd`，整块不可见的 s2 后缀块不再生成任务（一级：任务级裁剪）；保留的块内
> softmax/MM 列宽进一步按 `s2VisCols`（该块实际可见列数，64 对齐）收窄（二级：块内
> 列宽裁剪）。非因果路径逐项退化为原实现。

> **已验证锚点：** MHA 20 case 求和 3581→3160us（**1.133x**，K-Search 采纳解，
> 2026-08-25 终验 20/20 精度+长序列 12/12）；分 case：case7/8（B4_S1024_Skv1024_N32
  causal）548→421.7us（-23.1%）、case9（B4_S1024_D256 causal）-19.6%、case2 -39.6%、
  case5 -36.6%、case10 -20.0%；cann-bench 综合得分 90.41→94.02（平均加速比
  1.38x→1.51x）。

---

## 1. 优化原理

### 1.1 性能问题模式

右下角对齐因果（`is_causal=true`，block `j > i + (S_kv - S)`）下，Q 块只需看到
kv 列前缀：Q 块首行的可见终点 ≈ `qRowStart + (S_kv - S)`。原实现每任务扫全部
`ceilDiv(S_kv, s2BaseSize)` 个 s2 块——对 S=1024 causal，前 7/8 的 Q 块后半 s2 块
**整块不可见**，矩阵/向量/搬运/流水槽全部空转。已有 vec1 逐行算术掩码
（ApplyMask）保证正确性但省不了任何工作量。

### 1.2 核心公式（kernel-only，host 零改动）

```cpp
// 一级：任务级裁剪（mha_kernel.h CreateTask）
// 联合可见终点 visEnd（exclusive，绝对 kv 列坐标）——取块内最后一行的保守并集
uint32_t visEnd = curKvSeqLen;                       // 非因果 = 全可见
if (isCausal) {
    int64_t endI = (int64_t)qRowStart + qRows + (int64_t)curKvSeqLen - (int64_t)curQSeqLen;
    endI = clamp(endI, 1, (int64_t)curKvSeqLen);     // 防御性限幅
    visEnd = (uint32_t)endI;
}
curS2OuterBlocks = CeilDiv(visEnd, s2BaseSize);      // ceilDiv 保住含任一可见列的边界块

// 二级：块内可见列宽（同函数，逐任务写入 task）
task.s2VisCols = min(AlignUp64(visEnd - s2Start), s2BaseSize);  // delta 下限 1 防御
```

下游联动（`mha_vec.h`/`mha_cube.h`）：vec1 的 `outerCols`、SoftmaxFlashV2 的
`srcShape.srcK`、DataCopy 列数、MM1/MM2 的 Fixpipe `dstStride` 与 P 读取列宽全部
改读 `task.s2VisCols`；`s2Rows` 同步取 `min(s2VisCols, kvSeqLen - s2Start)`。
**64 对齐的来源**：s2BaseSize 本身按 64 对齐（SoftmaxFlashV2 srcK 约束同源），
`AlignUp64` 保证收窄后仍满足；不满足会走 WithTail 崩溃路径。

### 1.3 本策略利用的硬件机制

| 机制 | 利用方式 |
|---|---|
| 任务调度 | 完全不可见块在 CreateTask 处不进 runInfo——零调度/零矩阵/零向量/零同步开销 |
| 矩阵流水 | 边界块列宽收窄 → MM1 n 循环、Fixpipe 写出、MM2 k 轴分块同步变短 |
| 向量流水 | vec1ChunkRows 按 visCols 重算（8192/visCols），softmax/cast 的 tileSize 缩小 |
| online softmax | 裁剪不改变保留块的处理顺序与状态链（首末块标志以裁剪后任务数为准） |

## 2. 正确性红线

- **visEnd 必须取块内全部行的保守并集**：用块末行 `qRowStart+qRows-1`，禁止按块首行
  推导（会漏掉块内后续行的可见列）。公式里 `+qRows` 即"末行+1"。
- **矩形相对偏移必须显式在场**：`(S_kv - S)` 项不可省（Sq<Skv 的 MTP/交叉场景），
  不能假定两条序列同起点。
- **ceilDiv 保边界块**：含任一可见列的块必须保留；禁止四舍五入丢块。
- **边界块内保留原逐元素掩码**：块级裁剪不替代 vec1 的 ApplyMask，二者互补
  （裁剪删整块，ApplyMask 处理边界块内 j>visEnd 的散列）。
- **非因果路径必须逐字退化为原实现**：`visEnd=kvSeqLen` 时 `s2VisCols=s2BaseSize`、
  `curS2OuterBlocks` 与原公式字面相同——non-causal case 的回退即检测器。
- **在线归并链一致性**：isFirstVec1/isLastVec2 以裁剪后任务数推导；全裁空（理论上
  causal 域内 visEnd≥qRows≥1 不会发生）仍需合法空路径。
- state/P/AccO 的 ring 槽位按 loop 轮转，裁剪不改变槽位数学（任务少了槽位照常轮转）。

## 3. 泛化条件

- **适用**：结构化单调掩码（因果右下/左下对齐、可由序列位置推导连续可见前缀）；
  S_kv 越长、Q 块越靠前收益越大（S=Skv=1024 causal 理论工作量约减半）。
- **不适用**：非因果/任意稀疏/数据相关掩码；Sq>Skv 的场景需先核对掩码语义。
- **与 s2 分块的关系**：s2BaseSize 封顶（如 2048）后 S_kv 大的场景本就有多块，
  裁剪直接删后缀块；二者正交叠加（本锚点即为封顶+裁剪的组合）。

## 4. 实施步骤

1. `mha_kernel.h` CreateTask 内加 visEnd 推导与 `curS2OuterBlocks` 替换（约 15 行）。
2. RunInfo 增 `s2VisCols` 字段，CreateTask 写入。
3. `mha_vec.h` ComputeVec1：outerCols/srcK/tileSize/s2Rows 改读 s2VisCols；
   vec1ChunkRows_ 若按 s2BaseSize 预计算需改为按块重算或取 min。
4. `mha_cube.h` ComputeMM1/MM2：Fixpipe dstStride、K/V 装载列宽、P 读取列宽联动。
5. ApplyMask 的 validI 计算保持原样（它已含 s2Start 偏移，与 visEnd 语义一致）。

## 5. LLM 前置问题

- 当前任务生成是否对每个 Q 块遍历全部 s2 块？causal 下 Q 块首行可见终点公式？
- vec1 的 chunk 行数、SoftmaxFlashV2 srcK、Fixpipe dstStride 当前从哪些字段推导？
- 非因果路径改动后是否逐字节等价（diff 验证）？
- D=256 路径上 s2VisCols 收窄后 vec1ChunkRows 与 SM_STATE_ALIGN 的交互是否复核？

## 6. 风险与回退（含已实证的坑）

- **D256 小序列回退（已实证）**：case4（B2_S256_Skv256_N8_D256 causal）26.3→63.5us
  （**+142%**）。机理待定位（假设：visCols 收窄→vec1ChunkRows=8192/visCols 增大→
  与 subBlockRows/SM_STATE_ALIGN 交互劣化，或 SoftmaxFlashV2 在 D256+窄 srcK 命中
  低效 tiling）。**验收时 D256+短序列 causal case 必须单独核对**；可疑时对
  `D>128 且 visCols<s2BaseSize` 关闭二级裁剪（保一级）。
- 跨块归并的 prevSlot 链依赖任务连续性：裁剪后同 Q 块的保留块仍连续（只删尾），
  不破坏链；若未来实现中段裁剪需重审。
- 回退旋钮：`isCausal!=0` 分支整体删除即回原实现；host 侧无任何耦合。

## 7. 验收标准

- 精度：cann-bench compare_tensors 20/20（含 bf16/非二次幂 S_kv/zero-input）；
  长序列回归 12/12（S_kv 至 32768 × causal/non-causal/decode/D256）。
- 性能：causal 长序列 case 提升 ≥15%（本锚点 case7/8 达 23%）；非因果 case 变化
  在 ±2% 噪声内（退化检测器）；**D256 小序列 case 单列核对无 >5% 回退**。
- cann-bench 综合分对齐（本锚点 94.02）。

## 检索卡（短卡）

动作：为每个Q块计算保守联合可见终点visEnd，停止为整块不可见的s2后缀生成任务。
适用：掩码具有结构化单调性，可由序列位置推导连续可见前缀。
限制：visEnd必须覆盖Q块全部行的保守并集，应按块末行推导，禁止使用块首行。
范围：因果注意力kernel的CreateTask任务生成路径。
检索词：visEnd、Q块、KV列、s2后缀块、任务级裁剪、因果掩码、连续可见前缀
机会：每个Q块只可见连续KV前缀，后方存在整块不可见的s2任务。
