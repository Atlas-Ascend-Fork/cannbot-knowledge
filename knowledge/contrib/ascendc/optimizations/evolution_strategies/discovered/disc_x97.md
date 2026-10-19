---
type: Optimization
title: "逐 token 串行 scan 的『门控/标量壳』清零与向量体遍数收敛（门控链整片外提 + 同管全屏障 N→1 + 内层 Ps×NP 读写遍数压到算法下界）"
description: "不是由向量体吞吐决定时，呈三组并列信号之一（同一算子 12 例 sample pipeline 实测，单轮采样）："
tags:
  - task.optimization
  - topic.compute.reduction
  - topic.implementation.pipeline
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# Strategy X97: 逐 token 串行 scan 的「门控/标量壳」清零与向量体遍数收敛

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> schema_version: okf.v1
> kind: discovered_strategy
> id: X97
> title: "逐 token 串行 scan 的『门控/标量壳』清零与向量体遍数收敛（门控链整片外提 + 同管全屏障 N→1 + 内层 Ps×NP 读写遍数压到算法下界）"
> origin: discovered
> discovered_round: 3
> discovered_from: "33_Mamba2Fwd evolution round_3/parallel_1 (node n3_s1_s1) + round_2/parallel_2 (node x0_x1)（compat 副本，真源见 OKF）"
> base_speedup: "同窗/同协议 A/B 锚（非跨窗绝对数）：子杠杆 a+b = 变体 25.1371us vs 其父 26.6846us = 1.0616x（逐 case quick、device 0、min-of-2、同窗口）；子杠杆 c = 25.361us vs 起点 30.855us（同会话同协议链路 30.855→28.209→26.815→25.361）；逐 case 方向一致（c8 -24% / c6 -22% / c5 -32%，即 vec-主导例）。绝对 geomean 区间 25.1~25.8us（baseline 46.886us ⇒ 1.82~1.87x），置信度中：本机存在间歇性劣化窗口（见 failure-pattern f29），故不以跨窗绝对倍率为硬结论"
> confidence: single_op
> status: active
> op_families: [ssm, chunk-scan, recurrent, linear_attention, gla, elementwise]
> bottlenecks: [scalar_compute, no_overlap, partial_overlap, sync_overhead, near_optimal]
> tags: [per-token-shell, gate-chain-hoist, slab-vectorization, pipe-all-collapse, pass-count-floor, algorithmic-lower-bound, broadcast-tmp-sizing, brcb-row-reuse, vector-pass-minimization, 910b2c, dav-c220, mamba2, ssm, no-syncall]
> strategy_ids: [X97, X78, P94, P95, P99, X77, X58]
> reuse_stats:
>   ops: [33_Mamba2Fwd]
>   families: [ssm/recurrent(chunk-scan)]
>   passed: 1
> ```

## 判定信号

**逐 token / 逐 step 串行 scan**（SSM / 线性递归 / chunk-scan 逐 token 形态）的向量核，其 per-token 墙钟
不是由向量体吞吐决定时，呈三组并列信号之一（同一算子 12 例 sample pipeline 实测，单轮采样）：

- **scalar 头名**：`aiv_scalar_ratio 0.38~0.46`（vs `aiv_vec_ratio 0.27~0.34`）⇒ 标量壳偏厚；
- **两个 MTE 管都低**（`mte2 0.13~0.21`、`mte3 0.09~0.15`）而 `AIV 占 Task Duration ≈ 55~60%` ⇒ 非搬运受限；
- **vec 头名但已到遍历下界**：`aiv_vec_ratio 0.43~0.51` 且逐 token 内层对状态矩阵的**读写 pass 数已等于
  「递推 + 读出 + 归约 + 原位缩放」的算法下界**（本算子 = 4 遍）⇒ 再削向量体没有空间。

反面判据：若 per-token 归约维 L 很长且实现为 `for(i<L) s += buf.GetValue(i)` 形态的标量 FADD 链，
则**先用 X78**（分组保序向量归约）；本卡针对的是「不存在该 L 长链、但门控/预处理仍是 per-token 标量壳」的形态。

## 三个子杠杆（机制不同，可叠加，逐项单独 A/B）

**(a) 门控/预处理链整片外提（gate-chain slab hoisting）**
把挂在 token 循环里的门控链（本算子：`dt.GetValue(GM)` → softplus → clamp → `a=exp(dt'·A)`，每 token
约 15 步标量/向量混合 + 6 次 V↔S 往返 + 2 道全屏障）整体前移为 **token-slab 整片向量化**：
一次 1D 连续突发读入 `[nrows, H]`（`nrows = min(64, 1024/H)`）→ 升 fp32 → 整片 softplus/clamp/exp →
片内每个 token 只读 2 个 UB 标量。数值上与 per-token 形态逐位同构（同一公式、同一结合序）。

**(b) 同管全屏障收敛（N→1）**
per-token 的 `PipeBarrier<PIPE_ALL>` 由 **3 道收敛到 1 道**，另 2 道改由**每片一次**的定向 `V_S` 交接覆盖。
★红线：**不要一刀切删屏障**（f21：非确定挂死）；只把「每 token 都付」的全计量屏障换成「每片付一次」的定向事件。

**(c) 内层向量 pass 数压到算法下界**
逐 token 内层对状态矩阵 `S[Ps,NP]` 的整块读写 pass 从 **8 压到 4**（= 递推 + 读出 + 归约 + 原位缩放的算法下界）。
本算子实测三个动作：
- **删掉 B/C 的两次 Broadcast**：列广播由 level-0 `vmul`/`vmla` 的 `src1RepStride=0`「行复用」免费完成，
  不必物化 `[Ps,NP]` 广播张量；x 行广播改为先 `Muls(dt'·x)` 再广播，状态更新用 `vmla` 一步（连中间张量
  `prod` 都不写）；D 残差 `Mul+Add` 两步并一步。
- **放大 Broadcast 共享 tmp**：v220 实现 `oneRepeateSize = tmpElems/8`，每轮 = 1 `Brcb` + 1 `Copy` +
  2 道 `PIPE_V`；`Ps=64` 时 tmp 从 256B 放大到 4096B ⇒ 8 轮收成 1 轮（省 8 `Brcb` + 8 `Copy` + 16 道 V 全排/token）。
- **`Brcb` 消灭最后一次行广播 sweep**：`Brcb` 直接产出「每行一个标量」的块形态（块 p = `[xs[p]×8]`），
  配 `src0BlkStride=0` 让第 p 行整行取 `xs[p]`，行广播张量彻底不写。

> ⚠️ 子杠杆 (c) 的第三项会把乘积结合序从 `dt'·(x·B)` 改成 `(dt'·x)·B`。本次该改写经官方判据通过（50/50），
> 且与 `model.py` 的 torch 参考链 `dtr*x*Bh` 同序、单次 `vmla` 舍入；但**改结合序需逐案证据**（对照 f19）。

## 收益与证据（口径纪律）

| 子杠杆 | 同窗/同协议 A/B | 逐 case 方向一致性 | 绝对数 |
|---|---|---|---|
| (a)+(b) 门控链外提 + 屏障 3→1 | 1.0616x（变体 25.1371us vs 父 26.6846us，同一次协议 min-of-2） | 12 例中 **9 例变快**（c6 -19.8%、c0/c5 -11.3%、c8 -8.4%） | 区间参考 |
| (c) 内层 pass 8→4 + Broadcast/Brcb 优化 | 同会话链路 30.855→25.361us（4 步，每步同协议） | vec-主导例降幅最大（c5 -32%、c8 -24%、c6 -22%） | 区间参考 |

**绝对 geomean 只作区间**：该算子 baseline asc geomean 46.886us（本会话干净窗口，12 例），优化后
**25.1~25.8us ⇒ 1.82~1.87x vs baseline（vs PyTorch 口径 16.9~17.2x）**。置信度 **中**：
- 干净窗口同窗 A/B（父本复制进变体目录、一起测）= **1.82x**；冻结 PyTorch ref 口径 geomean = **1.87x**；
  劣化窗口同窗 A/B = 2.20x（上界）。
- 本机存在**间歇性劣化窗口**（failure-pattern f29：同一份 pristine 基线内核 c9 由 65.3us 抬到 1006us =
  15.4x，ref 侧 65x，且标称频率下无可见共租户）⇒ 绝对数不要跨窗引用。

## 适用场景

- 逐 token 串行 scan 的**纯 AIV/向量**实现（SSM/GLA/GDN/Mamba2 系），per-token 有门控/预处理标量链；
- 该算子**cube 不可用或不可达**（本算子每 token 的矩阵运算是 `M=Ps/K=NP/N=1` 的 matvec + 秩-1 外积，
  cube 化在 matmul 预算极小时是回归，见 failure-pattern f25 / canonical `scan-ssm-chunk-cube-cv-fusion` 的别信项）；
- 且**本构建下 SyncAll 挂死**（f21），故所有优化必须**核内自包含**（本卡的三个子杠杆全部满足）。

## 实现要点 / 红线

1. **保序**：(a)(b) 必须与 per-token 形态逐位同构；(c) 的第一/二项逐位相同，第三项改结合序需单独证据。
2. **槽基址 32B 对齐**：(a) 新增的第二个 slab 缓冲，其**片基址推进必须 round 到 32B**，否则硬报
   `UB address accessed by the VEC instruction is not aligned`（全核崩）。
3. **scratch 尺寸按 API 真实需求算**：(a) 抬高 UB 布局会挤掉尾部空闲区，暴露下游 API 的 scratch 真实需求
   （`reduce_sum_dyn` 的 `sharedTmpBuffer` 实际需约 `Ps*NP*4`，硬编码 16384 只够 `Ps<=64`）——见 f40。
4. **UB 预算先行**：pass 合并 + slab 缓冲会同时抬高 UB 占用，按最大 `PP/NP` 先算再动手。
5. **屏障只换不删**：把「每 token 全计量屏障」换成「每片定向事件」；一次性删光 = f21 非确定性挂死。

## 与相邻卡的关系

- **X78**（逐 token 串行 scan 的**标量归约链**清零）：X78 的前置是存在 L 长标量 FADD 链；本卡是其
  **互补形态**——不存在该链、但门控/预处理仍是 per-token 标量壳时用本卡。两者可组合（归约链长的算子先 X78）。
- **X95**（DMA 描述符数/块数 KPI）：正交可叠加——X95 削搬运描述符（本算子实测 1.076x），本卡削标量壳与向量 pass。
- **X77**（输出依赖图驱动的 barrier 消除）：本卡 (b) 是其在「每 token 全屏障」形态上的特化。
- **X58**（N=1 matvec 链归约 / PipeBarrier 松弛）：本卡 (c) 与 X58 的 Broadcast 消标量 / 屏障松弛同源。

## 来源

33_Mamba2Fwd evolution（进化基线内核模式，3 轮 × 3 并行 = 9 变体，全部过官方 50/50 判据）：
- round_3/parallel_1（node n3_s1_s1，strategy_guided，sc=[P66,P10,X78,P94,P95]）落地 (a)+(b)；
- round_2/parallel_2（node x0_x1，open_exploration）落地 (c)；
- 主 agent 独立复跑官方 `evaluate_ascendc.sh`：50/50 PASS（对全部 9 个变体中的 7 个逐次复核）。
