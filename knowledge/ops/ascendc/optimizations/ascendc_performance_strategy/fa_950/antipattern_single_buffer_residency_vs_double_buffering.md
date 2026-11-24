---
type: Optimization
title: 用"单缓冲驻留"换取搬运请求数（牺牲双缓冲）
description: 反模式：把分片多次 GM→L1 装载改成单缓冲 TBuf 整块常驻省请求数，实测两可信刻度均 0 收益（−0.04%），勿做。
tags:
- task.optimization
- topic.attention
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/06-antipattern-single-buffer-residency-vs-double-buffering.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 反模式策略：用"单缓冲驻留"换取搬运请求数（牺牲双缓冲）

> **单一反模式：** 当看到某个操作数被分片多次从 GM 装载到片上（`for k: LoadNd(GM→L1, 分片k)`）时，很自然的想法是"一次性把整块装进片上常驻，把 N 次请求降为 1 次"。**但若原实现使用的是深度 ≥2 的 `TQue`（自动双缓冲），改成单缓冲 `TBuf` 常驻就会拆掉 load/compute 重叠**——省下的请求数换不回丢掉的流水重叠。
>
> **结论：❌ 不要做。** 已实测，两个可信刻度均为 **0 收益（−0.04%，噪声内）**，且在真正触发的 shape 上机制上讲不通收益。
>
> **本策略的价值有二：**
> 1. 记录这条路已被证伪，避免重复尝试；
> 2. 提炼出**动手前必须先算的量**——本例的根本错误是"没算 `kTiles` 在目标 shape 上的实际取值就动手"，导致对**一半用例而言这是恒等变换**。

---

## 1. 反模式的样子

### 1.1 诱人的表象

```cpp
// 原实现：K 维分片装载，每片一次 GM→L1
for (uint32_t ki = 0; ki < kTiles; ++ki) {
    auto tile = tileQue_.AllocTensor<T>();               // TQue<A1, 2> —— 深度 2
    LoadNdGmToNzL1(tile, srcGm[off + ki * TILE], rows, TILE, ld, rowsAlign);
    tileQue_.EnQue(tile);
    tile = tileQue_.DeQue<T>();
    // ... LoadData(L1→L0) + Mmad ...
    tileQue_.FreeTensor(tile);
}
```

观察到：
- 每片的 `dValue = TILE`（如 128），源侧每行只连续 `TILE × sizeof(T)` 字节（如 256B）；
- 同一块数据被访问 `kTiles` 次。

于是想改成：

```cpp
// "优化"：一次装满，K 循环内取切片视图
LocalTensor<T> full = fullBuf_.Get<T>();                 // TBuf —— 单缓冲
SetWaitFlag<HardEvent::MTE1_MTE2>();                     // 手工双向闭环
LoadNdGmToNzL1(full, srcGm[off], rows, fullWidth, ld, rowsAlign);
SetWaitFlag<HardEvent::MTE2_MTE1>();
for (uint32_t ki = 0; ki < kTiles; ++ki) {
    auto tile = full[ki * TILE * rowsAlign];             // 零 GM 访问
    // ... LoadData(L1→L0) + Mmad ...
}
```

看起来：GM→L1 请求数从 `nTiles × kTiles` 降到 `nTiles`，且单次读退化为连续大块。

### 1.2 为什么不成立

**问题一：对很多 shape 而言这是恒等变换。**

`kTiles = K维长度 / TILE`。若目标 shape 的 K 维长度**恰好等于** `TILE`（实例：`Dk=128`，`BLOCK_N=128`），则 `kTiles == 1`——原实现本来就是"每块一次、`dValue = 128 = 全宽"的满行读**，所谓"重复访问 kTiles 次"根本不存在。

实例中 7 个 perf 用例里有 3 个（含两个主力刻度）都是 `Dk=128`，即改动对它们是**恒等变换**。实测 −0.04% 正是"代码等价"的应有结果。

**问题二：对真正触发的 shape，拆掉了双缓冲。**

原 `TQue<A1, 2>` 深度为 2，k-tile 之间**天然双缓冲**：

```text
     MTE2: load(k=0) │ load(k=1) │ load(k=2) │
     MTE1/M:         │ mmad(k=0) │ mmad(k=1) │ mmad(k=2)
                      ↑ 重叠      ↑ 重叠
```

改成单缓冲 `TBuf` 后，为保证跨轮复用正确性必须加 `MTE1_MTE2` / `MTE2_MTE1` 双向硬闭环，于是：

```text
     MTE2: ─────── load(整块) ───────│
     MTE1/M:                         │ mmad(0) mmad(1) mmad(2)
                                     ↑ 整块必须全部落地才能发第一条 Mmad
```

**整个块的 MTE2 必须全部完成，才能发出第一条 `Mmad`。** 省下的请求数（如 4→1）换不回丢掉的 load/compute 重叠。

---

## 2. 实测数据

A5(Ascend950DT) SparseFlashAttention，A/B 同二进制（环境变量开关切换）：

| 用例 | Dk | kTiles | 关闭 | 开启 | Δ |
|---|---|---|---|---|---|
| prefill_bsnd_gqa_b2_s256 | 128 | **1** | 1735.5 | 1734.8 | −0.04%（恒等变换） |
| prefill_bnsd_gqa_b2_s1024 | 128 | **1** | 15505.5 | 15498.9 | −0.04%（恒等变换） |
| decode_bsnd_mla_b32 | 512 | 4 | 27.45 | 27.84 | +1.4%（噪声带内，不可判读） |
| decode_bnsd_mla_dk576 | 576 | 4 | 43.13 | 43.66 | +1.2%（同上） |

两个可信刻度停在 −0.04%，即**零收益**。

---

## 3. 何时"整块常驻"才是对的

本策略否定的是"**用单缓冲换请求数**"，不是否定"整块常驻"本身。以下情形整块常驻**是对的**：

| 情形 | 说明 |
|---|---|
| 该操作数**跨外层循环复用** | 如 Q 在整个 topK chunk 链中不变——装载一次供多轮使用，收益来自"跨轮复用"而非"合并请求" |
| 常驻后仍保留双缓冲 | 容量允许开两块整块 buffer 交替 |
| 原实现本就是单缓冲 | 不存在"拆掉双缓冲"的代价 |
| 该装载**不在关键路径** | 如预取阶段，重叠与否不影响总时长 |

判别问题：**"我是在减少请求数，还是在增加复用次数？"**
- 增加复用次数（同一份数据被更多轮使用）⇒ 真收益。
- 只是把 N 次请求合成 1 次、总字节数不变、复用次数不变 ⇒ 大概率是本反模式。

---

## 4. 动手前必须先算的量（本策略的核心教训）

| 必算量 | 为什么 |
|---|---|
| **`kTiles` 在每个目标 shape 上的实际取值** | 若 `kTiles == 1`，改动是恒等变换，白做 |
| 原实现的 buffer 深度 | 若 ≥2，改单缓冲会拆掉双缓冲 |
| 改后能否保留双缓冲 | 容量是否允许两块整块 buffer |
| 该操作数是否跨轮复用 | 决定收益来源是"复用"还是"合并请求"（§3） |
| 该装载是否在关键路径 | 不在则无收益 |

> **教训（可推广到所有优化）**：**先把病灶在目标 shape 上的实际取值算出来，再动手**。
> 本例的错误是照着代码结构"看到有循环就想合并"，而没算 `kTiles` 实际等于几。
> 这与"把气泡拍成 200ns 就算出 4.9% 的诱人收益"（策略 07）是同一类错误：
> **用未经验证的假设做定量推断。**

---

## 5. 若已经做了，如何判定要不要回退

| 观察 | 结论 |
|---|---|
| 可信刻度 Δ 在噪声带内（如 ±0.5%） | 零收益，回退（保持代码简洁与双缓冲） |
| 只有 `kTiles == 1` 的 shape 无变化 | 符合预期（恒等变换），看 `kTiles > 1` 的 shape |
| `kTiles > 1` 的 shape 劣化 | 双缓冲被拆掉，回退 |
| `kTiles > 1` 的 shape 明显改善 | 例外情形，保留但须复测 ≥3 次确认 |

回退时注意：单缓冲版本引入的手工 `MTE1_MTE2`/`MTE2_MTE1` 闭环也要一并删除，否则残留无用同步。

---

## 6. 附带教训：不要顺手删"看起来没用"的 buffer

实施本反模式时，为腾出容量，曾把一个"自某次重构后已无任何 `AllocTensor`/`DeQue` 消费点"的 `TQue` 删除——静态看是纯粹的死代码。

**结果：某用例精度稳定失败**（`max_abs 5.43e-3` 越过 fp16 容差 `5e-3`，`mismatch 0.00%`，三次复现一致）。回退该删除后立刻恢复。

**归因**：删掉一个 `TQue` 会改变 TQue 隐式分配的**事件 ID 编号**，而该 kernel 中另有 buffer 使用**无显式 eventID** 的 `SetWaitFlag<HardEvent::...>()`。ID 重排后与 TQue 内部事件交叠，破坏了那块 buffer 的跨轮复用闭环 ⇒ 读到上一轮的陈旧数据。

误差量级（归一化后的小偏差、`mismatch ≈ 0`）也与"少量陈旧数据"而非"逻辑错"吻合。

**结论：这类 kernel 中 TQue 的数量本身是同步契约的一部分。** 删 buffer 属**行为变更**而非清理；要动必须同时把手工 `SetWaitFlag` 改成显式 `FetchEventID` 分配的事件。

---

## 7. 验收标准（若要复核本结论）

```bash
# A/B 必须同二进制（用编译期/运行期开关切换），排除构建差异
bash <build> --soc=<soc> --op=<op> --wheel
for i in 1 2 3; do <run perf>; done     # 每态重复 ≥3 次
```

判据：

- 先确认各 shape 的 `kTiles` 值，**只看 `kTiles > 1` 的 shape**；
- `kTiles == 1` 的 shape 应**完全无变化**（否则说明改动越界了）；
- 若 `kTiles > 1` 的 shape 无改善或劣化 ⇒ 本反模式成立，回退。

结论须写清：

```text
本条为已证伪的反模式：用单缓冲常驻换请求数，实测 0 收益。
根因一：对 kTiles==1 的 shape 是恒等变换（动手前未算 kTiles）。
根因二：对 kTiles>1 的 shape 拆掉了 TQue 深度 2 的天然双缓冲。
"整块常驻"本身不错，错在"用牺牲双缓冲的方式换请求数"——
判别问题：我是在增加复用次数，还是只在合并请求？
```

## 检索卡（短卡）

动作：反模式：把分片多次 GM→L1 装载改成单缓冲 TBuf 整块常驻省请求数，实测两可信刻度均 0 收益（−0.04%），勿做。
适用：动手前必算 kTiles 实际取值（==1 即恒等变换）、原 TQue 深度、能否保留双缓冲、是否跨轮复用。
限制：kTiles==1 时改动是恒等变换；原 TQue 深度≥2 时改单缓冲须 MTE1_MTE2/MTE2_MTE1 硬闭环，整块落地才发 Mmad。
范围：K 维分片装载的矩阵乘 kernel。
检索词：TQue、TBuf、双缓冲、kTiles、MTE1_MTE2、MTE2_MTE1、恒等变换、LoadNdGmToNzL1。
机会：看到 for k 分片装载想一次装满常驻、GM→L1 请求数从 N 降 1；判别问题：是在增加复用次数还是只合并请求。
代价：拆掉 load/compute 重叠；顺手删 TQue 会改事件 ID 编号致精度稳定失败。
