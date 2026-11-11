---
type: Optimization
title: "X81: Kc 单块化（恢复被 TEMP 覆盖的 host tiling）"
description: "逐 token 串行 scan 型向量核中，host 的 K 维分块常量若被硬编码临时值覆盖，块循环次数会成倍增加并重复读取同一输入；恢复宿主原生分块可令 nKb=1，并需同步重定尺归约 workLocal、保持控制字段打包槽位并重算 UB 预算。"
tags:
  - task.optimization
  - topic.compute.reduction
  - topic.tiling
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X81: Kc 单块化（恢复被 TEMP 覆盖的 host tiling）

## 核心思路

逐 token T 串行 scan 型向量核里，若 host 的 K 维分块常量被一个硬编码/临时值（注释常带
TEMP / TODO / 调试痕迹）覆盖，则每步的块循环次数 `nKb = ceil(Kp/Kc)` 会从 1 变成多块：
**每一步都要把同一份输入（sdec / q / k / b）按块再从 GM 读一遍**，并在很小的微 tile 上重发
Cast / Broadcast / ReduceSum。因为逐 token 链是串行的，这些重复工作全部落在关键路径上，
是「每 token 固定开销」里最容易被低估的一块。

把 Kc 恢复为宿主本来要算的值（`Kc = min(Kp, max(16, (4608/max(Vp,16))/16*16))`）后 `nKb = 1`，
块循环与重复读消失，每条向量指令覆盖的元素数随之增大。

**必须配套三件事**，否则恢复 Kc 本身会引入 bug 或精度事故（见「实现要点」）。

## 适用场景

- 逐 token / 逐 step **串行** scan / 递推 / adjoint 型向量算子，且 K 维被分块（`nKb > 1`）。
- 判定信号（grep 即可）：host tiling 里「先算出 Kc、紧随一行硬编码覆盖」的形态（注释常带
  TEMP / TODO / 调试痕迹）；或 per-step 成本随 `nKb` 近似线性增长。
- K/V 规模不大且非 16 对齐、不适合上 Cube 的纯 Vector 路径。
- 每块 dS 累加器已常驻 UB（分块只是为了让 workLocal/UB 放得下小 tile，而非算法必需）。

## 实现要点

1. **归约 workLocal 必须随 kvSize 重定尺**：`reduceTmpBuf_` 之类的 UB 临时区若按旧的小 tile 硬定尺，
   恢复 Kc 后 ReduceSum 的 workLocal 会**溢出到相邻 UB buffer**并静默污染它（数值上表现为
   max_abs_diff 明显增大）。改成 `max(kvSize, Kp) * sizeof(float)` 后归约结果恢复正常。
   **这是静默精度事故，不报错、只在数值上体现。**
2. **host 控制字段的打包槽位不要迁**：若 host 把 phase/nChunks 之类的控制字段打包进同一个 int 参数，
   它的容量通常能容纳恢复后的 Kc。把打包迁到另一个参数槽会让 Init 的**形参与成员同名遮蔽**，
   按打包值分配 UB → `VEC instruction error: the ub address out of bounds`。
3. **UB 预算按新 kvSize 重算**（确保最坏占用仍小于 UB 容量 192KB）；`arShape/raShape/bcast*Shape` 等
   由 `this->Kc` 派生的形状变量要确认自动跟随。
4. **核间均衡顺手做**：nChunks 的选择加一条「`totalTasks % aivCoreNum == 0` 优先」的候选。
5. **精度口径**：任何 Kc 改动都会重排「跨 Kb 块归约」的求和分组，低精度输出**必然**出现 1~2 ULP 偏差；
   可用 Kc 回退对照实验区分「kernel 侧改动是否 bit 中性」。

## 验证方法

- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。

## 补充判据（跨算子复核）

- **把“clamp / legacy 常量”加入审计清单**：除 TEMP 覆盖外，还要检查参数 clamp 的上下限是否还有真实依据。例：某 UB 页号缓存遗留的 `clamp(..., 2, 64)` 在 gather 改为直接标量读后已无依据，却仍把 slot 数压到 64，导致 slot 数翻倍、每 slot 尾部 drain 占比升高；放行到容量上限后 pipeline 效率从约 83% 升到约 91%。
- **判据**：任何 clamp 常数都要能指向一个仍然存在的资源约束；找不到就按容量上限重算，并用同窗 A/B 验证。
