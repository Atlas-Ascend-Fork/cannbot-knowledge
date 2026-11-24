---
type: Optimization
title: cube/vec 跨核软件流水——producer stage 当前 tile 先发，再等上一 tile consumer 的跨核 flag
description: 将主体由 consumer(wait) 在前改为 producer-first，先发当前 tile 的生产阶段。
tags:
- task.optimization
- topic.attention
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/07-cube-vec-pipeline-producer-first-overlap.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：cube/vec 跨核软件流水——producer stage 当前 tile 先发，再等上一 tile consumer 的跨核 flag

> 单一优化点：在 cube(AIC)/vec(AIV) 混合核的软件流水里，一个 producer cube stage（把 matmul 结果写到 GM workspace）和一个 consumer cube stage（从该 workspace 读再 matmul）经由跨核 flag 与 vec stage 交接。把 cube 主体的指令顺序排成「先发当前 tile 的 producer stage，再去等上一 tile consumer stage 的跨核 flag」，使 producer 的重 cube 工作（片外加载→matmul→fixpipe）在 scalar 等跨核 flag 期间、以及 vec stage 在另一类核上执行期间并行——形成真 3 级 overlap。配套硬要求：跨 stage 复用的 operand 必须放在按 tile 逻辑槽索引的双缓冲 on-chip buffer 里，否则 producer 会覆写 consumer 尚未读完的 operand。

## 1. 原理

一个 tile 在该流水线下经过三个 stage（分布在不同核 / 不同时刻）：
- **producer stage**（cube）：用本 tile 输入做 matmul，结果写到 workspace 的一个槽。
- **vec stage**（vec 核）：读该槽、做向量计算（如逐元素非线性 / 统计重算），写回另一组 workspace 槽。
- **consumer stage**（cube）：读 vec 写回的槽，再做 matmul，产出最终输出。

相邻 tile 的这三个 stage 可以 overlap：tile T 的 producer、tile T-1 的 vec、tile T-1 的 consumer 同时进行。但这只在该流水线**主体指令顺序**正确时才成立。

关键：cube 核在一个循环 iteration 里同时负责「发当前 tile 的 producer」和「drain 上一 tile 的 consumer」。consumer stage 的第一条指令是**等 vec 把上一 tile 写完的跨核 flag**。这条 wait 会**阻塞 scalar 核**（不是 cube 计算单元）。

- **错误顺序（串行化）**：iteration 里先做 consumer（其起手即跨核 wait）再做 producer。则 scalar 先卡在等 vec 完成上一 tile，**之后**才发当前 tile 的 producer——producer 与 vec 永远不 overlap，流水退化成「cube-producer → vec → cube-producer → vec」的串行乒乓。
- **正确顺序（producer-first）**：iteration 里先发当前 tile 的 producer（其 cube 工作：片外加载、matmul、fixpipe 进入计算单元的流水），**然后**再做 consumer 的跨核 wait。这样 producer 的 cube 计算在 scalar 被 wait 阻塞时仍在计算单元上推进，同时 vec 在另一核跑——真 3 级 overlap。

## 2. 性能问题模式

适用本策略的典型病征：
- profiler 显示 cube 核与 vec 核的 wall-clock 都很大、且 task 接近二者最大值，看似「两核并发」；
- 但每个核的 wall-clock 里都掺了大量「每 tile 等对方」的空等（单核 wall-clock 远大于其计算单元真实忙碌时间）；
- 已经把 workspace 做成多槽乒乓、已经有跨核 flag 交接，**但 task 持平不降**——因为主体顺序是「drain 上一 consumer 的 wait → 再发当前 producer」，把本该 overlap 的 stage 串行了；
- 换更深的工作区槽数 / 更多 flag 也不改善（因为问题在 issue 顺序，不在槽位数量）。

反例（不适用）：单 stage 无跨核交接；或 producer/consumer 之间无 vec 中间 stage、无跨核 wait（无 overlap 可挖）；或 operand 无跨 stage 复用（见下，双缓冲非必需）。

## 3. 正确性红线

**核心反模式（禁止）**：主体绝不能排成「先 drain 上一 tile consumer 的跨核 wait，再发当前 tile producer」——consumer 起手的跨核 wait 会先把 scalar 阻塞在等 vec 上，导致 producer 与 vec 零 overlap，流水线退化为串行（收益归零，等于没优化）。即便下面的双缓冲、flag、尾 tile 全做对，只要主体顺序错了，性能不降反可能因多槽开销变差。必须严格 producer-first（见 §1、§5）。这是本策略最容易做反的一步，务必在实现与验收时显式核对主体顺序。

1. **operand aliasing（最易踩）**：跨 stage 复用的 operand（producer 加载、consumer 仍需读的输入）必须放在**按 tile 逻辑槽索引的双缓冲**里：producer 写槽 `tileIdx % 2`，consumer 读槽 `(tileIdx-1) % 2`——两个不同 buffer。若用单成员变量，producer(tile T) 会在 consumer(tile T-1) 读前覆写它 → 数值错（多 tile 场景必现）。双缓冲容量：2 × (复用 operand 集合) 须 ≤ on-chip buffer 上限。
2. **flag 配对与 slot 生命周期**：跨核 flag 的 set/wait 严格配对；workspace 槽的复用距离（槽被重写前经过的 tile 数）必须 ≥ 流水深度，保证 consumer 读完才被 producer 重写。
3. **多 vec 子核的 gather 语义**：若一个 cube 核对应多个 vec 子核，cube 一次 set flag 广播释放所有子核；cube 的 wait 须汇聚（所有子核都 set 才放行）——这是 slot 复用安全的保证（所有子核写完才解锁重写）。
4. **尾 tile 覆盖**：prologue 单独发 tile 0 的 producer；循环体覆盖 tile 1..n-1；epilogue 单独 drain tile n-1 的 consumer。漏末 tile 会导致 consumer 死等一个永不 set 的 flag（整体 hang）。
5. **空核兜底**：无任务的核仍须参与全核同步，否则有任务的核会在同步点永久阻塞。

## 4. 泛化条件

**适用**：
- cube/vec 混合核（一类核做 matmul、另一类做向量），且存在 producer→vec→consumer 的三 stage 流水；
- producer 与 consumer 经 GM workspace + 跨核 flag 交接（非寄存器直传）；
- 跨 stage 有 operand 复用（producer 加载的输入 consumer 还要用）。

**不适用**：
- 纯 cube 或纯 vec、无跨核交接；
- producer/consumer 无中间 vec stage（无可 overlap 的第三方）；
- 跨 stage 无 operand 复用（双缓冲非必需，单缓冲即可，但仍可受益于 producer-first 顺序）。

**前置**：该算子已有 depth-2 乒乓 workspace + 跨核 flag（本策略是把 depth-2 升级为真 depth-3 overlap + 配套双缓冲 operand，而非从零搭流水）。

## 5. 实施步骤

1. **读现有主体顺序**：确认 cube 循环体里 producer 与 consumer(wait) 的相对顺序。若 consumer(wait) 在 producer 之前 → 命中本策略。
2. **改主体为 producer-first**：
   ```text
   prologue: producer(tile 0); set cross-core flag(tile 0)
   body t = 1 .. n-1:
     producer(tile t); set cross-core flag(tile t)   # 先发：cube 计算单元开跑
     wait cross-core flag(tile t-1 from vec)         # 后等：scalar 阻塞，但计算单元仍在忙 producer(t)
     consumer(tile t-1)
   epilogue: wait flag(tile n-1); consumer(tile n-1)
   ```
3. **跨 stage 复用 operand 升双缓冲**：把 producer 加载、consumer 仍需的每个 operand 的 on-chip buffer depth 提到 2，按 `tileIdx % 2` 选槽；consumer 用 `(tileIdx-1) % 2` 那槽、末尾释放。核对 2 × operand 集合 ≤ buffer 上限。
4. **核对 flag 配对 / slot 复用距离 / 多子核 gather / 尾 tile / 空核同步**（见 §3）。
5. 不改动各 stage 内部的 matmul/向量化计算逻辑，只改跨 tile 的 issue 顺序与 operand 缓冲深度。

## 6. LLM 前置问题

- 当前 cube 循环体里，producer stage 与 consumer stage（含其跨核 wait）的相对顺序是什么？consumer 的 wait 是否排在 producer 之前？
- producer 加载的 operand 里，哪些 consumer 还要用（跨 stage 复用）？它们现在放在单成员变量还是多槽缓冲？
- 跨核 flag 是乒乓（2 组）还是更多？flag 复用周期与 workspace 槽复用距离是否匹配？
- 一个 cube 核对应几个 vec 子核？flag 是广播+汇聚吗？
- workspace 槽深度、on-chip buffer 剩余容量能否容纳 2 × 复用 operand 集合？

## 7. 验收标准

- **构建通过**。
- **精度**：全量精度套件通过，**重点含多 tile 多核场景**（tile 数 ≥ 3、非对齐尾 tile、单 tile 边界）——operand aliasing / 尾 tile / slot 生命周期 bug 都会在多 tile 暴露。
- **性能**：相对未优化基线，task 显著下降；且 cube 核与 vec 核的 wall-clock **同向下降**（证明 overlap 把每 tile 空等转成了有用工作，而非只挪了瓶颈）。
- 若 task 不降、单核 wall-clock 不动 → 主体顺序未真正 producer-first（仍串行）或无 vec 中间 stage 可 overlap，本策略不适用。

## 检索卡（短卡）

动作：将主体由 consumer(wait) 在前改为 producer-first，先发当前 tile 的生产阶段。
适用：cube/vec 混合核中存在 producer→vec→consumer 三阶段流水。
限制：禁止先等待并排空上一 tile 的 consumer，再发当前 tile producer。
范围：cube/AIC 与 vec/AIV 混合核的逐 tile 流水。
检索词：producer-first、consumer wait、GM workspace、跨核 flag、三阶段流水。
机会：循环主体中 consumer(wait) 排在 producer 之前。
