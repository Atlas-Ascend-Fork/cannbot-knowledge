---
type: Optimization
title: "逐 token 串行 scan 的『门控/标量壳』清零与向量体遍数收敛（门控链整片外提 + 同管全屏障 N→1 + 内层 Ps×NP 读写遍数压到算法下界）"
description: "逐 token 串行 scan 的向量核若 per-token 墙钟不由向量体吞吐决定，常表现为标量/门控壳偏厚、MTE 管利用率低或向量 pass 已到算法下界。把门控/预处理链整片外提、同管全屏障 N→1、内层状态读写 pass 压到算法下界，可显著降低 per-token 固定开销。"
tags:
  - task.optimization
  - topic.compute.reduction
  - topic.implementation.pipeline
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X97: 逐 token 串行 scan 的「门控/标量壳」清零与向量体遍数收敛

## 判定信号

**逐 token / 逐 step 串行 scan**（SSM / 线性递归 / chunk-scan 逐 token 形态）的向量核，其 per-token 墙钟
不是由向量体吞吐决定时，呈三组并列信号之一：

- **scalar 头名**：`aiv_scalar_ratio` 明显高于 `aiv_vec_ratio` ⇒ 标量壳偏厚；
- **两个 MTE 管都低**而 AIV 占 Task Duration 较高 ⇒ 非搬运受限；
- **vec 头名但已到遍历下界**：`aiv_vec_ratio` 较高且逐 token 内层对状态矩阵的**读写 pass 数已等于
  「递推 + 读出 + 归约 + 原位缩放」的算法下界**（如 4 遍）⇒ 再削向量体没有空间。

反面判据：若 per-token 归约维 L 很长且实现为 `for(i<L) s += buf.GetValue(i)` 形态的标量 FADD 链，
则**先用 X78**（分组保序向量归约）；本卡针对的是「不存在该 L 长链、但门控/预处理仍是 per-token 标量壳」的形态。

## 三个子杠杆（机制不同，可叠加，逐项单独 A/B）

**(a) 门控/预处理链整片外提（gate-chain slab hoisting）**
把挂在 token 循环里的门控链（例如 `dt.GetValue(GM)` → softplus → clamp → `a=exp(dt'·A)`）
整体前移为 **token-slab 整片向量化**：
一次 1D 连续突发读入 `[nrows, H]`（`nrows = min(64, 1024/H)`）→ 升 fp32 → 整片 softplus/clamp/exp →
片内每个 token 只读 2 个 UB 标量。数值上与 per-token 形态逐位同构（同一公式、同一结合序）。

**(b) 同管全屏障收敛（N→1）**
把每 token 的 `PipeBarrier<PIPE_ALL>` 收敛为**每片一次**的定向 `V_S` 交接，避免每 token 重复付全量屏障。
★红线：**不要一刀切删屏障**（非确定挂死）；只把「每 token 都付」的全计量屏障换成「每片付一次」的定向事件。

**(c) 内层向量 pass 数压到算法下界**
逐 token 内层对状态矩阵 `S[Ps,NP]` 的整块读写 pass 压到 **4 遍**（= 递推 + 读出 + 归约 + 原位缩放的算法下界）。
三个动作：
- **删掉 B/C 的两次 Broadcast**：列广播由 level-0 `vmul`/`vmla` 的 `src1RepStride=0`「行复用」免费完成，
  不必物化 `[Ps,NP]` 广播张量；x 行广播改为先 `Muls(dt'·x)` 再广播，状态更新用 `vmla` 一步（连中间张量
  `prod` 都不写）；D 残差 `Mul+Add` 两步并一步。
- **放大 Broadcast 共享 tmp**：v220 实现 `oneRepeateSize = tmpElems/8`，每轮 = 1 `Brcb` + 1 `Copy` +
  2 道 `PIPE_V`；放大 tmp 后多轮 Brcb/Copy 可收成一轮，减少每 token 的 V 全排。
- **`Brcb` 消灭最后一次行广播 sweep**：`Brcb` 直接产出「每行一个标量」的块形态（块 p = `[xs[p]×8]`），
  配 `src0BlkStride=0` 让第 p 行整行取 `xs[p]`，行广播张量彻底不写。

> ⚠️ 子杠杆 (c) 的第三项会把乘积结合序从 `dt'·(x·B)` 改成 `(dt'·x)·B`。该改写必须经全量精度判据
> 且与 torch 参考链同序；**改结合序需逐案证据**。

## 适用场景

- 逐 token 串行 scan 的**纯 AIV/向量**实现（SSM/GLA/GDN/Mamba2 系），per-token 有门控/预处理标量链；
- 该算子**cube 不可用或不可达**（每 token 的矩阵运算极小，cube 化在 matmul 预算极小时是回归）；
- 且若构建下 SyncAll 不可用，则所有优化必须**核内自包含**（本卡的三个子杠杆全部满足）。

## 实现要点 / 红线

1. **保序**：(a)(b) 必须与 per-token 形态逐位同构；(c) 的第一/二项逐位相同，第三项改结合序需单独证据。
2. **槽基址 32B 对齐**：(a) 新增的第二个 slab 缓冲，其**片基址推进必须 round 到 32B**，否则硬报
   `UB address accessed by the VEC instruction is not aligned`（全核崩）。
3. **scratch 尺寸按 API 真实需求算**：(a) 抬高 UB 布局会挤掉尾部空闲区，暴露下游 API 的 scratch 真实需求
   （例如 `reduce_sum_dyn` 的 `sharedTmpBuffer` 实际需约 `Ps*NP*4`，硬编码固定大小只够较小 `Ps`）。
4. **UB 预算先行**：pass 合并 + slab 缓冲会同时抬高 UB 占用，按最大 `PP/NP` 先算再动手。
5. **屏障只换不删**：把「每 token 全计量屏障」换成「每片定向事件」；一次性删光 = 非确定性挂死。

## 与相邻卡的关系

- **X78**（逐 token 串行 scan 的**标量归约链**清零）：X78 的前置是存在 L 长标量 FADD 链；本卡是其
  **互补形态**——不存在该链、但门控/预处理仍是 per-token 标量壳时用本卡。两者可组合（归约链长的算子先 X78）。
- **X95**（DMA 描述符数/块数 KPI）：正交可叠加——X95 削搬运描述符，本卡削标量壳与向量 pass。
- **X77**（输出依赖图驱动的 barrier 消除）：本卡 (b) 是其在「每 token 全屏障」形态上的特化。
- **X58**（N=1 matvec 链归约 / PipeBarrier 松弛）：本卡 (c) 与 X58 的 Broadcast 消标量 / 屏障松弛同源。

## 验证方法

- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
- 屏障收敛类改动额外做连跑压力测试，确认无死锁；pass 合并类改动核对最大 `PP/NP` 下的 UB 占用与 scratch 需求。
