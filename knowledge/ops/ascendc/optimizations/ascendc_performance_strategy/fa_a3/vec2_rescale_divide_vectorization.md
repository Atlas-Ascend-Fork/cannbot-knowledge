---
type: Optimization
title: Vec2 rescale/divide 标量循环改 Brcb 广播向量化
description: 把 Vec2 逐行 GetValue 标量读取+逐行 Muls/Divs，改为 Brcb 广播行状态后用 RowMuls/RowDivs 向量化。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/14-vec2-rescale-divide-vectorization.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：Vec2 rescale/divide 标量循环改 Brcb 广播向量化

> **单一优化点：** 对向量后处理阶段（Vec2）的 per-row rescale（按 online-softmax 的 max 重缩放跨块累加输出）与 divide（按 sum 归一化），把 `GetValue(row)` 标量读取行状态 + 逐行 `Muls`/`Divs` 的标量循环实现，改为 `Brcb`（硬件广播）把标量行状态（max/sum）广播到整个行块，再用 `RowMuls`/`RowDivs`（或整块 `Muls`/`Divs`）一次向量化处理整个行块。不改变 chunk 调度、不改 softmax 数学、不新增缓冲层级。

> **已验证锚点：** 在 attention-like 前向（online softmax + 跨 KV 块累加输出）上，把 Vec2 逐行标量 rescale/divide 换成 `Brcb + RowMuls/RowDivs`，精度与标量实现逐位等价或仅舍入差异（只改实现不改公式），Vec2 段耗时下降，典型端到端增量约 5–8%。收益来自向量单元填充率提升、标量-向量切换开销消除，以及省去"把行状态拷到 staging UB + `V_S` barrier"的额外拷贝。

本策略只做"rescale/divide 标量换向量"一件事。改变行块大小（chunk）、改变 softmax 公式/合并顺序、改变状态存放位置、改变输出 dtype/布局都**不属于**本策略，必须作为独立实验。

---

## 0. 范围声明

保持不变：

- rescale/divide 的数学公式、online 合并顺序、归一化语义与最终输出布局。
- 矩阵阶段、L0/L1 微块尺寸、reduce 分块、跨核任务划分。
- 逐行状态（max/sum）的存放位置、生命周期与 slot 语义。
- 向量后处理的 chunk 行数与队列深度（属行块合并策略）。

允许的最小改动：

- Vec2 rescale/divide 的实现从 `GetValue` 标量循环改为 `Brcb` 广播 + `RowMuls`/`RowDivs`（或整块 `Muls`/`Divs`）。
- 必要时新增/调整一个广播 UB 缓冲（`AlignUp(chunk, BRCB) × BRCB × F`）作为 `Brcb` 展开区。

不属于本策略：

- 改 chunk 行数或队列深度（行块合并策略）。
- 迁移逐行状态的 GM/片上位置（onchip state cache / state direct cache write 策略）。
- 改 P-ready 信号时机（Vec1 early P-release 策略）。
- 改矩阵 tiling、流水线或 L0 双缓冲。

---

## 1. 性能问题模式

基础形态：Vec2 对每个输出行做 rescale（把历史累加输出按 `exp(max_old − max_new)` 重缩放）和 divide（按 sum 归一化）。若用标量实现：

```text
for r in 0 .. chunk_rows:
    m = GetValue(state_max, r)        # 标量读 max
    s = GetValue(state_sum, r)        # 标量读 sum
    factor = exp(m_old[r] − m)        # 标量 exp
    Muls(O[r, :], factor)             # 逐行标量缩放
    Divs(O[r, :], s)                  # 逐行标量归一化
```

问题：

- 每行一次标量读 + 标量乘/除，`chunk_rows` 行串在向量流水上，标量单元与向量单元交替阻塞。
- 常见实现还要先把行状态从 state UB 拷到 staging UB 再逐行用，多一次拷贝 + `V_S` barrier。
- 行块越宽（每行 `dim` 大），逐行标量循环的相对开销越显著。

优化目标：用 `Brcb` 一次广播行状态到整块，用 `RowMuls`/`RowDivs` 一次向量化整块，消除标量循环与额外拷贝。

---

## 2. 适用条件

必须同时满足：

| 条件 | 要求 |
|---|---|
| 标量实现 | Vec2 rescale/divide 当前用 `GetValue(row)` + 逐行 `Muls`/`Divs` 标量循环（若已是 `Brcb`/`RowMuls` 向量路径，本策略无增量） |
| 行间独立 | rescale/divide 对每一行独立，行间无前后依赖，整块向量化不改变行间语义 |
| 状态在 UB | 行状态（max/sum）已在 UB 中按行可读（`Brcb` 源）；若在 GM，先做 onchip state cache / state direct cache write |
| UB 有余量 | 能容纳广播展开缓冲 `AlignUp(chunk, BRCB) × BRCB × F`（与现有 UB 占用合计不超限） |
| 行对齐 | chunk 行数与起点满足 `Brcb` 的行粒度要求（尾块按有效行处理） |

优先场景：profiling 显示 Vec2 标量开销或标量-向量切换占比可见；行块较宽、`chunk_rows` 较大。

不适合：rescale/divide 已向量化；行状态不在 UB 且无法先迁移；UB 已满无法容纳广播缓冲；Vec2 标量开销本就可忽略（收益低于测量噪声）。

---

## 3. 优化变换

基础（标量循环）：

```text
for r in 0 .. chunk_rows:
    m = GetValue(state_max, r); s = GetValue(state_sum, r)
    O[r, :] = O[r, :] * exp(m_old[r] − m) / s        # 逐行标量
```

优化（Brcb 广播 + 向量）：

```text
max_bcast = Brcb(state_max, chunk_rows)              # max 广播成 chunk_rows × row_width
sum_bcast = Brcb(state_sum, chunk_rows)              # sum 同理
O = RowMuls(O, exp_of(m_old_bcast − max_bcast))     # 整块按行向量缩放
O = RowDivs(O, sum_bcast)                            # 整块按行向量归一化
```

关键点：

- `Brcb` 把 per-row 标量（max/sum）广播成与 `O` 同形状的块，按行对齐。
- `RowMuls`/`RowDivs` 按"每行一个标量因子"广播乘/除整块，数学上与逐行标量乘/除等价。
- `exp` 因子若参与 rescale，按原公式计算（标量 per-row `exp` 或整块向量 `exp`，二者舍入可能不同，须验证精度）。

---

## 4. 正确性约束

- **行对齐**：广播状态严格按行对齐，不跨行错位（`Brcb` 行粒度 + chunk 行数对齐）。
- **数学等价**：只把"逐行标量乘/除"换成"整块按行广播乘/除"，不改变每行的缩放因子与运算顺序。
- **舍入一致性**：标量 `Muls` 与向量 `RowMuls`、标量 `exp` 与向量 `exp` 的舍入路径可能不同，须用精度阈值验证（REL ~1e-3），不能假设逐位相同。
- **尾块**：最后行块有效行数 `< chunk` 时，广播与向量指令只作用于有效行，padding 不写入最终输出。
- **不改语义**：不改变 online 合并顺序、scale、mask、累加顺序、输出 dtype/布局。
- **连续环形流水场景下的 RowDivs 安全限制**：当 Vec2 的 `inputQue1_`/`VECIN` 队列 slot 张量因连续环形流水进入长寿命状态时，对该 slot 张量**原地执行 `RowDivs`（广播写）会写出垃圾数据**（见 KP-026）。修复：新分配 `AllocTensor`（`outputQue_`）作为 divide 目标，不可对 VECIN slot 原地广播写。标量 divide 路径（`GetValue` + `Divs`）不受此限制。

---

## 5. 实施步骤

1. 定位 Vec2 的 rescale/divide：找到 `GetValue(state_max/sum, row)` + 逐行 `Muls`/`Divs` 的标量循环。
2. 确认行状态在 UB（若在 GM，先做 onchip state cache / state direct cache write）。
3. 用 `Brcb` 广播 max/sum 到行块；用 `RowMuls`/`RowDivs`（或整块 `Muls`/`Divs`）替换标量循环。
4. 预算广播 UB 缓冲 `AlignUp(chunk, BRCB) × BRCB × F`，确认与现有 UB 占用合计不超限。
5. 编译 + 精度（重点验证 exp/乘除的舍入差异）+ 性能对比。

不要在同一轮同时做：改 chunk 行数、改状态位置、改 P-ready 时机、改矩阵 tiling —— 拆成独立实验，避免收益/风险归因混淆。

---

## 6. 验证流程

静态自检：

- rescale/divide 数学公式与标量实现一致（仅实现换向量）。
- 广播缓冲行对齐、尾块有效行。
- UB 总占用（含广播缓冲）≤ 上限。

动态验证：

- 精度：与标量实现同阈值（REL ~1e-3，mismatch 0%），数值应逐位等价或仅舍入差异；重点跑"多 KV 块累加触发 rescale"的 case（`exp(max_old − max_new)` 路径）。
- 性能：Vec2 段耗时下降；端到端增量 ≥ 1% 才保留，否则视为无显著收益并回滚。
- 边界 shape：尾块行数 < chunk、多 head、不同 dim、不同 KV 块数。

---

## 7. 与其他策略的关系

- **与行块合并（s6）正交互补**：行块合并减少 chunk 数（调度），本策略改每个 chunk 内 rescale/divide 的实现（标量→向量）。组合时在行块合并后的更大行块上做 `Brcb` 广播，收益叠加；二者也可分别独立应用。
- **依赖状态可读**：rescale/divide 需按行读 max/sum，状态在 UB 时 `Brcb` 源可直接用；若状态在 GM，先做 onchip state cache / state direct cache write。
- **不改 P-ready 时机**（Vec1 early P-release）、不改矩阵/流水线/L0 双缓冲（s9–s13）。

---

## 8. 回滚规则

| 失败类型 | 信号 | 处理 |
|---|---|---|
| 精度失败 | rescale/divide 段误差超阈值（多为 exp/乘除舍入差异） | 回标量实现，或把 exp 单独保留标量 per-row |
| UB 超限 | 广播缓冲导致 UB 超限 | 缩 chunk（属行块合并策略范围）或回标量 |
| 性能无收益 | Vec2 标量开销本就低，向量化后端到端 <1% | 回滚，标记本算子不适用 |

---

## 9. 文档自检

- 未包含具体算子名、源文件名、函数名。
- 未包含 AscendC 实现代码片段。
- 只使用伪代码、抽象 helper、适用条件、验证流程与回滚规则。
- 硬件参考值（BRCB 粒度、UB 容量）使用通用表达，不含特定算子参数。

## 检索卡（短卡）

动作：把 Vec2 逐行 GetValue 标量读取+逐行 Muls/Divs，改为 Brcb 广播行状态后用 RowMuls/RowDivs 向量化。
适用：GetValue+逐行标量实现；行间独立；行状态在 UB 可读；UB 容纳 AlignUp(chunk,BRCB)×BRCB×F。
限制：环形流水下不可对 VECIN slot 原地 RowDivs，须 AllocTensor 新目标；标量与向量舍入可能不同须验证；尾块只作用有效行。
范围：online-softmax 跨块累加输出的向量后处理环节。
检索词：Brcb、RowMuls、RowDivs、GetValue、V_S barrier、online softmax、VECIN。
机会：每行标量读+乘除使标量与向量单元交替阻塞；行状态拷 staging UB 多一次拷贝+barrier。
代价：新增广播 UB 缓冲占用；exp 向量与标量舍入可能不同。
