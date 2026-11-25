---
type: Optimization
title: "已验证方案：纯 AIV 五段归约流水的「并行度塌陷」修复（PPSA 续跑）"
description: "纯 AIV 五段归约流水的并行度塌陷修复：按输出行/列切分并折叠部分和，使每段吃满可用核数，而不是只改单段内部循环。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/tiling_strategy/inter_core_load_balance.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/overhead_optimization/core_count_kernel_type.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/ppsa_5stage_parallel_collapse_fix.json
    role: evidence
created_at: "2026-10-29T00:00:00Z"
updated_at: "2026-10-29T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 ppsa-5stage-parallel-collapse-fix）。
>
> 原始元数据：
>
> ```yaml
> id: ppsa-5stage-parallel-collapse-fix
> op_families: [reduction, elementwise, attention]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/ppsa_5stage_parallel_collapse_fix.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/ppsa_5stage_parallel_collapse_fix.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# 已验证方案：纯 AIV 五段归约流水的「并行度塌陷」修复（PPSA 续跑）

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 问题现象

五段流水（K1 praw/rowpart → K2 softmax_hw+weff → K3 sppre/zpart → K4 s/u/LN → K5 out）里：

| 段 | grid | 「大 C + 小 HW + 小 B」case（C 640~2048，nblk 1~2，B 1~5）上的实况 |
|---|---|---|
| K2/K4 | `B` | 1~8 个核；单核要读满 4 个 `c2×C` fp32 权重矩阵（C=2048 时共 33.6MB ≈ 1.1ms） |
| K1/K3/K5 | `B*nblk` | 1~16 个核；48 核里空转 32~47；每 task 内 `for c0 step 8` 有 C/8 = 20~192 轮迭代 |

⇒ **不是带宽，是「并行度 × 每迭代/lanch 固定开销」**。

## 方案（四刀，全部 fp32 累加、无原子、无跨核 flag）

1. **通道轴切片 + 消费者折叠**（X118 形态）：pass kernel 任务表从 `(b, blk)` 扩为 `(b, blk, kc)`，
 每核只走 `C/ncs` 个通道；hw 索引的归约量（praw、sppre）落 `praw_part[b,ci,hw]` / `sppre_part[b,ci,hw]`，
 由**消费者**（K2 的 softmax 扫描、K5 的 sigmoid 前）对 ncs 个切片求和 —— 不新增 combine kernel。
 `rowpart/zpart` 天然按通道独立，无需折叠。通道块起点按 32B（8 float）对齐，步长在 host/device 间显式传递。
2. **matvec 按输出行/列切分**：s/q2/weff/u 各自独立成 launch，按输出行切给 48 核（读连续 slab，无 strided）；
 每核从 GM 重算所需的 per-batch 小向量（xm、z，≤0.6MB，常驻 L2，重算几乎免费）。
 `c2` 的 softmax 与 `C` 的 LayerNorm 是全局归约 ⇒ 必须用 kernel 边界断开（最便宜的 barrier）。
3. **权重按原生 dtype 传入，UB 内 Cast 到 fp32**：删掉 host 侧 12 次 `.to(at::kFloat)`（每次 forward 都执行），
 fp16/bf16→fp32 是精确转换，逐 bit 等价；4 个 `c2×C` 矩阵的 GM 流量减半，且少 12 个 ~2us 的 Cast kernel。
4. **LayerNorm 下沉到 out 段** + `R = min(1024, AlignUp(HW,64))` 自适应 HW tile + 所有 tile 循环改软件流水
 （先发下一块 DMA 再算当前块）。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/ppsa_5stage_parallel_collapse_fix.json`；引用时请结合上文适用条件与失效边界判断适用范围。

## 适用条件与陷阱

- 适用：纯 AIV 多段归约流水（通道/空间注意力、极化自注意力、门控、per-channel 归一化），
 且 kernel 里出现 `grid = b` 或 `grid = b*ceil(n/NB)` 这类「小 n 时退化成 b」的形态。
 必须按 `perCore = 4*c2*C*bytes/B > 150KB` 门控双路径（见 X191）。
- **不要试图减 pass**：3 遍 x 是数学下界——要压到 2 遍须让 `chw` 在第 2 遍已知，而 chw 依赖全局归约 z
 （又依赖第 2 遍本身）；唯一出路是把 proj_b 的 x slab 常驻 UB（C=2048 时需 8MB vs UB 192KB）。不可行。
- **不要用 GM 原子**：分片缓冲 + 单消费者求和在确定性上严格优于 AtomicAdd，且无 32B 对齐陷阱。
- `Pattern::Reduce::RA` 在此布局下被否证（workspace ≈2B/元素撑爆 UB，且行 stride ≠ padLast 时结果错），
 见 F28；行和请用「一次 2-D DMA + 向量 Add 链」或 `ReduceSum<AR>` 且保证 stride 与 padLast 一致。
- Cube 化（P102）仍是带宽墙（F18），本轮无人采用且复核一致。

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。
