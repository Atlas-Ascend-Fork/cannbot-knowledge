---
type: Optimization
title: "X81: Kc 单块化（恢复被 TEMP 覆盖的 host tiling）"
description: "逐 token T 串行 scan 型向量核里，若 host 的 K 维分块常量被一个硬编码/临时值（本例Kc = 16;  // TEMP，覆盖了它上方刚算好的原生 tiling）钉死，则每步的块循环次数nKb = ceil(Kp/Kc) 会从 1 变成 3~6：每一步都要把同一份输入（sdec …"
tags:
  - task.optimization
  - topic.compute.reduction
  - topic.tiling
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# Strategy X81: Kc 单块化（恢复被 TEMP 覆盖的 host tiling）

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> id: X81
> origin: discovered
> discovered_round: 3
> discovered_from: round_3/parallel_1
> base_speedup: 11.2134x
> ```

## 核心思路

逐 token T 串行 scan 型向量核里，若 host 的 K 维分块常量被一个硬编码/临时值（本例
`Kc = 16;  // TEMP`，覆盖了它上方刚算好的原生 tiling）钉死，则每步的块循环次数
`nKb = ceil(Kp/Kc)` 会从 1 变成 3~6：**每一步都要把同一份输入（sdec / q / k / b）按块再从 GM 读一遍**，
并在只有 512~768 元素的微 tile 上重发 Cast / Broadcast / ReduceSum。因为逐 token 链是串行的，
这些重复工作全部落在关键路径上，是「每 token 固定开销」里最容易被低估的一块。

把 Kc 恢复为宿主本来要算的值（`Kc = min(Kp, max(16, (4608/max(Vp,16))/16*16))`）后 `nKb = 1`，
块循环与重复读消失，每条向量指令覆盖的块从 512~768 元素涨到 1536~4608 元素。

**必须配套三件事**，否则恢复 Kc 本身会引入 bug 或精度事故（见「实现要点」）。

## 适用场景

- 逐 token / 逐 step **串行** scan / 递推 / adjoint 型向量算子，且 K 维被分块（`nKb > 1`）。
- 判定信号（grep 即可）：host tiling 里「先算出 Kc、紧随一行硬编码覆盖」的形态（注释常带 TEMP / TODO / 调试痕迹）；
  或实测「每多一个 nKb 块，per-step 成本约 +2us」的线性关系。
- K/V 规模不大（本例 ≤128）且非 16 对齐、不适合上 Cube 的纯 Vector 路径。
- 每块 dS 累加器已常驻 UB（分块只是为了让 workLocal/UB 放得下小 tile，而非算法必需）。

## 实现要点

1. **归约 workLocal 必须随 kvSize 重定尺**：`reduceTmpBuf_` 之类的 UB 临时区若按旧的小 tile 硬定尺
   （本例固定 `8*1024` 字节，恰好 = Kc 16 × Vp 128 × 4B），恢复 Kc 后 ReduceSum 的 workLocal 会**溢出到相邻 UB buffer**
   并静默污染它（本例污染 `sdecBuf_`，`dg` 的 max_abs_diff 达 482）。改成 `max(kvSize, Kp) * sizeof(float)`
   后 `dg` max_abs_diff 482 → 1.5e-5。**这是静默精度事故，不报错、只在数值上体现。**
2. **host 控制字段的打包槽位不要迁**：若 host 把 phase/nChunks 之类的控制字段打包进同一个 int 参数
   （本例 `KcPacked = Kc + 1000*phase + 10000*nChunks`），它的容量本来就能容纳恢复后的 Kc（Kc ≤ 128 完全放得下）。
   把打包迁到另一个参数槽（本例迁到 `nKb`）会让 Init 的**形参与成员同名遮蔽**（`nKb` 形参 vs `this->nKb`），
   按打包值分配 UB（实测 27MB）→ `VEC instruction error: the ub address out of bounds`。
3. **UB 预算按新 kvSize 重算**（本例最坏 ~138.5KB < 192KB 仍安全）；`arShape/raShape/bcast*Shape` 等
   由 `this->Kc` 派生的形状变量要确认自动跟随。
4. **核间均衡顺手做**：nChunks 的选择加一条「`totalTasks % aivCoreNum == 0` 优先」的候选
   （本例 case44 由 40 核 × 326 步改成 48 核 × 55 步/核 = 275 步/核）。
5. **精度口径**：任何 Kc 改动都会重排「跨 Kb 块归约」的求和分组，低精度输出**必然**出现 1~2 ULP 偏差
   —— 见 OKF failure pattern `f22`（含用 `Kc` 回退对照实验区分「kernel 侧改动是否 bit 中性」的做法）。

## 来源

自动发现于 Gdn2Bwd（GDN-2 chunkwise 反向 adjoint）进化 round_3/parallel_1（node sv2，进化基线）。
相对基线 kernel（to-PyTorch geomean 5.093x，case14 20370.9us / case44 25951.8us）提升 **2.20x**：
champion = **11.2134x vs PyTorch**（独立复测 device 14：case14 10330.3us = 9.293x、case44 10684.4us = 13.531x；
agent 自测 device 9：11.3658x，case14 10088.6us / case44 10649.0us）；相对基线 kernel 时 case44 单独 25951.8 → 10684.4us（2.43x）。
同一进化的上一任 champion（round_1/parallel_2，T 段切分 adjoint scan）为 6.9249x ⟹ 本策略在其之上再取 1.62x。
