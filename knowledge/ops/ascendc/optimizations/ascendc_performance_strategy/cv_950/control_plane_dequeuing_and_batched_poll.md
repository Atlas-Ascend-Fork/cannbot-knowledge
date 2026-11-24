---
type: Optimization
title: 控制面去标量化（队列簿记显式槽位化 / tiling 块搬 / 批量 flag 轮询）
description: 稳态循环的 staging 队列簿记换预分配槽位视图加最小 set/wait flag，tiling POD 改块搬进 TBuf，逐 flag 轮询改 32B 块批量轮询。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/cv-A5/39-control-plane-dequeuing-and-batched-poll.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：控制面去标量化（队列簿记显式槽位化 / tiling 块搬 / 批量 flag 轮询）

> **来源：A5 自由探索实测（gru_sigmoid_tanh_lerp，2026-09-14；stack_addmm，2026-09-14，107 裸机）**
> direction_key: `aic-scalar-kp-loop-overhead::tque-staging-elimination::kp-mma-inner-loop`（实例一）；`scalar-control-plane::vectorized-tiling-copy-and-batched-flag-polling::kernel-init-and-split-k-handshake`（实例二）
> 证据：<AOA_ROOT>/campaigns/gru-sigmoid-tanh-lerp-a5-107-20260912-opencode/framework/aoa_out/gru_sigmoid_tanh_lerp_custom/loop_<run-id>/explore/direction_003/
>       <AOA_ROOT>/campaigns/stack-addmm-a5-107-20260912-opencode/framework/aoa_out/stack_addmm_custom/loop_<run-id>/explore/direction_002/
> 实测：实例一 1.1436 x（geomean 34.182→29.889us，27 case 零回退；`aic_scalar` 绝对占用 -59%/-62%，`mte2` ratio 不变 → 归因孤立）24/24；实例二 1.0340 x（geomean 19.564→18.921us；AIV 侧 `aiv_scalar` ratio 逐 case 下降 g20 0.55→0.38、g2 0.76→0.61、g17 0.73→0.63）22/22。

## 原理

数据面贴顶后，top1 流水常常是**控制面**（`aic_scalar` / `aiv_scalar`）。三条独立削减，都保持数据落点与同步语义不变：

1. **队列簿记显式槽位化（实例一）**：稳态内层循环里，a2/b2/b1 三条 staging 队列每轮共 10 次 `AllocTensor/EnQue/DeQue/FreeTensor`，替换为循环前一次性预分配的 raw ping-pong 槽位视图 + 最小显式跨流水 set/wait flag（队列的 EnQue/DeQue 底层即同族原语，MTE1→M / MTE2→MTE1 定序语义逐对保留）；同时把循环不变量（尾段算术、`MmadParams`、搬运参数结构体字段）外提，仅保留与迭代索引相关的字段。
2. **tiling POD 块搬（实例二）**：把 32 次标量读的 tiling 参数拷贝改为 1~2 笔 MTE2 块搬进 TBuf，再本地读字段（AIV 侧）。
3. **批量 flag 轮询（实例二）**：顺序逐 flag 轮询改为 32B 块轮询——一次读 8 个 flag，按 `ceil(P/8)` 块做位掩码检查，每批一轮事件对；保留 write-once 标志语义、有界等待与生产侧 `dcci CACHELINE_OUT` 可见性契约。

## 性能问题模式（哪些 profiling 信号说明该用）

- 数据面（mac / vec / mte2）绝对时间不变或已贴顶，而 scalar 占比是 top1（实例一 `aic_scalar` 0.845→0.794 的起点即 top1；实例二 `aiv_scalar` 0.18~0.76 而 `aiv_vec` ≤0.10）。
- 内层稳态循环里每轮有固定次数的队列 API 调用（Alloc/EnQue/DeQue/Free）与参数结构体填充。
- kernel 初始化段与握手段有逐 flag 顺序轮询、逐字段标量读的形态（P 大时轮询次数线性放大）。
- 归因验证信号：改造后 scalar 占比显著下降**且**其它流水的绝对时间不变。

## 正确性红线（什么情况下禁止用 / 必须回退）

1. **本平台 AIC 核没有可用的 MTE2 GM→UB 通路**：AIC 侧尝试块搬会在 Init 阶段 aicore timeout（实测）。因此「tiling 块搬」只在 AIV 侧落地，AIC 侧保持标量拷贝——不要全平台照搬（实例二实测 AIC 半边不可实现，收益只来自 AIV 半边）。
2. **标志语义不得放宽**：write-once、有界等待、生产侧 `dcci CACHELINE_OUT` 可见性三者都要保持；批量轮询只是把「逐条读」变成「按块读 + 位掩码判定」，判定结果必须与逐条等价。
3. **预取时序不变**：队列簿记替换是「同族原语 + 定序逐对保留」的改写，不得顺手改双缓冲/预取的时序（与 08 号卡的调度兼容，只改管理方式）。
4. **尾批单独处理**：批量轮询的批宽必须处理 `P % 8 != 0` 的尾批，且不得退化成无超时自旋。
5. **不变量外提的作用域必须正确**：外提的字段必须在该循环内真为不变量（如仅与 kp 相关的字段必须留在循环内）；误提会改变数据地址或尾段长度。
6. **收益必须用归因孤立证据报**：只报总时长不足以证明是控制面削减；须给 scalar 绝对占用/占比的下降与该流水之外不变两项证据。

## 泛化条件（dtype / shape / pipeline / 算子类型）

- dtype：与 dtype 无关（控制面）。
- shape：内层迭代轮数多、P（分段/标志数）大的 case 收益最大；实例一 F=512 档 -25%、F=96 档仅 -4%（小档纯噪声）。
- 流水线：`aic_scalar` / `aiv_scalar`；对任何「稳态循环里带队列 API 簿记」或「kernel 初始化/握手段大量标量读」的 AscendC 内核适用。
- 与 13 号卡（AIV chunk 双缓冲）的关系：13 用 depth=2 队列构造流水，本条把队列簿记本身去掉（改用显式槽位 flag）；两者叠加时以本条的槽位视图承载 13 的深度语义。
- 与 39 号卡之外的控制面策略（如 04 号交接批量化）互补，不冲突。

## 实施步骤（从证据里的真实 diff 抽象成通用步骤）

1. 取得 scalar 流水的归因证据（占比 + 绝对时间），确认它是 top1 且数据面不再是瓶颈。
2. 数出稳态循环每轮的队列 API 调用次数；把队列换成循环前预分配的 raw ping-pong 槽位视图，逐对补回原有的跨流水定序 flag。
3. 外提循环不变量，逐字段确认作用域（仅迭代相关字段留在循环内）。
4. 初始化/握手段：AIV 侧的 POD 拷贝改块搬进 TBuf 后读字段；AIC 侧保持标量（红线 1）。
5. 逐 flag 轮询改按 32B 块批量轮询 + 位掩码判定，处理尾批，保留有界等待。
6. 全量精度用例通过后做配对测量，报 scalar 占比/绝对占用与该流水之外不变两组归因数据。

## LLM 前置问题（应用前必须自问）

1. scalar 是 top1 吗？绝对时间与占比各是多少？数据面是否已贴顶？
2. 稳态循环每轮的队列 API 调用次数是多少？换成槽位视图后定序语义靠哪些 flag 保留？
3. 这次改动会不会碰到 AIC 侧 GM→UB 块搬（本平台不可用）？
4. 标志轮询的语义（write-once/有界等待/可见性）在批量形态下如何等价？尾批怎么处理？
5. 外提的每个字段都确认过是循环不变量吗？
6. 归因证据是什么（scalar 下降 + 其它流水不变）？不看总时长能否证明机制成立？

## 验收标准（编译 / 精度 / 性能判据，含噪声底口径与回退阈值）

- **构建**：编译通过；槽位视图的地址与容量与队列形态等价。
- **精度**：全量用例通过、零修复轮（实测 24/24、22/22）；数值路径零改动（flag 定序逐对保留）。
- **性能**：配对 geomean 超噪声底（实测 1.1436x / 1.0340x）；小档形态允许落在噪声带。
- **归因**：scalar 绝对占用显著下降（实例一 -59%/-62%）**且** mte2/mac 绝对时间不变。
- **回退**：需要 AIC 侧块搬、标志语义无法等价、或外提字段作用域不确定时，回退原队列/逐条轮询路径。

## 检索卡（短卡）

动作：稳态循环的 staging 队列簿记换预分配槽位视图加最小 set/wait flag，tiling POD 改块搬进 TBuf，逐 flag 轮询改 32B 块批量轮询。
适用：数据面已贴顶、scalar 占比是 top1 的内核（稳态循环带队列 API 簿记或初始握手段大量标量读）。
限制：AIC 无可用 MTE2 GM→UB 通路（块搬只在 AIV 侧）；write-once/有界等待/dcci 可见性契约不变；尾批与外提字段须核验。
范围：内核控制面（队列簿记、握手段标量读、flag 轮询）。
检索词：TQue 去簿记、槽位 flag、循环不变量外提、tiling 块搬、TBuf、批量轮询、aic_scalar。
机会：数据面绝对时间不变而 scalar 占比 top1；内层循环每轮 10 次队列 API；P 大时逐 flag 轮询放大。
代价：须以归因孤立证据报收益（scalar 占用降、其它流水不变）。
