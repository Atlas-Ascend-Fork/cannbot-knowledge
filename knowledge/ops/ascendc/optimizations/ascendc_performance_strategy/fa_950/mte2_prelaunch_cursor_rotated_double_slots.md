---
type: Optimization
title: 内层 tile 的 MTE2 预发 + 游标轮转 depth-2 右操作数槽（PRELAUNCH gap=1）
description: 将右操作数即时单槽搬运改为MTE2预发，并以slot[2]和游标轮换双槽。
tags:
- task.optimization
- topic.attention
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/02-mte2-prelaunch-cursor-rotated-double-slots.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：内层 tile 的 MTE2 预发 + 游标轮转 depth-2 右操作数槽（PRELAUNCH gap=1）

> 状态：**proposal（未落地种子）**——2026-08-20 MLA K-Search run（round 12）World Model 自主派生，
> 因 S5 相位共享结构上的代码定位失败（empty diff, too_hard）未进入评测。机制描述完整，验证缺口见 §7。

单一优化点（针对「分块 Cube matmul 中 GM→L1 搬运（MTE2）与 L1→L0→Mmad（MTE1+MM）被 scalar 的即时
flag-wait 串行化」）：把内层 tile 循环里**随输出块重载的右操作数**（QK^T 的 K / P@V 的 V）的 MTE2
**发起点**从"消费前一行"提前到"循环顶部"——即消费 tile i 的 Cube MAC 之前就 issue tile i+1 的搬运；
用 cursor 轮转的 depth-2 A1 槽位承载，PRELAUNCH gap=1。**只改发起顺序，不改槽位数、不改任何 buffer
大小**——这是它与全量 S7（单 TBuf→TQue 深度软流水）的关键区别：实施面最小化，保证在复杂既有结构上
也能产出非空、可验证的 diff。

与存量策略的关系：`mla_strategries/07-cube-l1-multibuffer-soft-pipeline-mte2-mm-overlap.md`（S7）的
**第一步实现切片**。S7 要求把单 TBuf 整体重构为 TQue ping-pong 并删手工 SetWaitFlag，在已应用 S5（相位
共享 L1 buffer）的代码上 agent 常因结构对不上而 no-op；本策略把同一收益方向拆到"仅 issue 顺序"这一
最小维度，成功后可再沿 S7 加深。

## 1. 原理

- 串行化机理：右操作数单槽 + 即时 SetFlag/WaitFlag（Set 紧跟 Wait，硬屏障）时，scalar 发出 tile i 的
  MTE2 后必须在 flag 上空等搬运完成才能发 MTE1+MAC——MTE2（纯搬运）与 MTE1/MM（计算引擎）本可跨引擎
  并行，却被 host 侧同步顺序锁死，表现为 aic_scalar 占比异常高（60~85%）而 aic_mac 不高。
- 预发机理：depth-2 槽 cursor 轮转（slot[i%2]）下，循环顶部先 issue slot[(i+1)%2] 的 MTE2，再等 slot[i%2]
  的完成 flag 并消费（MTE1→MAC）。于是每次 Wait 等的是**已在途一个 tile 时长**的搬运，而非零起步的搬运
  ——单路重叠（gap=1），MTE2 与 MTE1/MM 跨引擎重叠被建立。
- 排序不变量（正确性的全部来源）：
  1. 任一 slot 的 MTE2 完成 flag 先于该 slot 的 MTE1 读（消费点 dequeue）；
  2. MTE1→MAC 链保持既有 queue 管理；
  3. 循环不变左操作数（Q/P 边）的独立 buffer 及其硬 SetFlag/WaitFlag 边界**原样保留**；
  4. 不新增跨核事件。
- 容量不变性：depth=2 槽即 S5 相位共享 kvL1 的均分（(k·blockW)·cols → 2×(blockW·cols/2) 视实现而定），
  或独立于相位共享区另设双槽——**总字节不增**是硬要求。

## 2. 性能问题模式

- profiling 指纹：aic_scalar_time 占比 60~85% 远高于 aic_mac_time；对标更快实现同 shape 下 scalar 占比
  显著更低（scalar-bound 指纹）；MTE2 引擎 busy 与 MM 引擎 busy 时间轴几乎不重叠。
- 代码指纹：内层 tile 循环体内"LoadData(右操作数) → SetFlag → WaitFlag → MTE1 → Mmad"严格相邻串行；
  右操作数每块重载、左操作数循环不变。
- 高发场景：N-blocks≥2 的分块 Cube matmul（attention 的 QK^T/PV、两段式 GEMM），尤其 prefill/长序列
  （本例 prefill_fp16_causal 2×512×2048 是 5-case 中唯一剩余 >4x 落后的 case）。

## 3. 正确性红线

- **不得只删同步不预发**：删掉手工 SetWaitFlag 却不建立预发顺序 = 数据竞态（MTE1 可能读到旧/空槽）。
- **MTE2↔MTE2 不重叠**：MTE2 引擎基本串行，预发只与 MTE1/MM 跨引擎重叠有意义；不要为"更深流水"在一
  个引擎上排两个 MTE2 然后指望它们并行（会劣化）。
- **循环不变左操作数不参与轮转**：hoist 语义保持单 buffer + 既有同步（对照 S7 AP-003：随块变化的右操作数
  "每块重载+overlap"可优于 hoist 一次，但循环不变操作数必须保持 hoist，不可套用本策略）。
- **相位共享契约（若在 S5 结构上实施）**：mm2 载 V 覆盖 K 之前的 SetWaitFlag<MTE1_MTE2> 语义不得被预发
  顺序破坏——预发 V 的 MTE2 必须排在该屏障之后，或把 K/V 纳入同一轮转域并证明互斥。
- **容量**：双槽总字节 ≤ 原单槽（或 S5 共享区）预算；depth 不得超过原单 buffer 覆盖块数 k（对照 S7 AP-002）。
- **尾块**：最后一次迭代的预发目标不存在，须 gap 收尾（不 issue 或 issue 后不等）；SetFlag 计数两侧
  对称，防 CrossCore 悬挂。

## 4. 泛化条件

- **适用**：所有"右操作数随输出块每块重载、左操作数循环不变"的分块 Cube matmul；scalar-bound 指纹明确
  （aic_scalar >> aic_mac）者优先；已应用 tile 放大（S5）后仍 scalar-bound 的 prefill 是首选靶点。
- **不适用**：右操作数循环不变（应 hoist，属另一策略）；N-blocks=1（无内层重载可预发）；MTE2 带宽已是
  主瓶颈（预发只改时序不改流量，带宽饱和时收益趋零）。
- **前置**：软依赖 S5/tile 放大（大 tile 才有足够长的 MAC 相位遮蔽搬运）；若目标代码无相位共享结构，
  独立双槽亦可。

## 5. 实施步骤

1. 定位内层 tile 循环中右操作数的 LoadData+SetFlag+WaitFlag 三连与消费点（MTE1/Mmad）。
2. 引入 `slot[2]` 与 cursor；循环顶部 issue slot[(i+1)%2] 的 MTE2（首发在循环外 preload slot[0]）。
3. 消费点改为 Wait slot[i%2] 完成_flag → MTE1 → MAC；消费后 slot 释放回 cursor。
4. 尾迭代：不预发（或预发空操作），保证 flag 计数对称。
5. 不动左操作数 buffer 与其同步；不动跨核事件。
6. 精度全过 → msprof 对比 aic_scalar 占比与 kernel 时长（N-blocks≥2 的 case）。

## 6. LLM 前置问题

- 内层循环里右操作数的 LoadData 在哪发出？Set 与 Wait 之间的距离（是即时屏障吗）？
- 左/右操作数哪个随块变、哪个不变？各自的 buffer 是 TBuf 还是 TQue？深度多少？
- 当前 aic_scalar 与 aic_mac 的占比？N-blocks（内层重载块数）是多少？
- 是否已应用 tile 放大/相位共享 L1？共享契约的屏障在哪一行？

## 7. 验收标准与验证缺口

- 验收：build + 精度全过；N-blocks≥2 的 case（本例 prefill_fp16_causal，当前 2413μs vs 对标 ~600μs）
  aic_scalar 占比下降且 kernel 时长下降；N-blocks=1 / decode 类 case 逐位等价不劣化（硬指标）。
- **验证缺口（本策略为种子未实测）**：收益幅度未标定（预期为 S7 历史量级的部分：prefill -11~50% 区间）；
  在 S5 相位共享结构上的屏障重排安全性未验证——首个落地者应重点核对 §3 第 4 条。
- 来源：`.ksearch-mla/20260820_191621/runs/20260820_111539/world_model/world_model.json` 节点 `s7a`
  （World Model 于 S7 no-op 后自主派生，difficulty 3，confidence 0.55）。

## 检索卡（短卡）

动作：将右操作数即时单槽搬运改为MTE2预发，并以slot[2]和游标轮换双槽。
适用：分块Cube matmul中右操作数随输出块重载、左操作数循环不变。
限制：实施前须核对MTE2预发、双槽生命周期和位置变换；不得仅删除同步而不预发。
范围：分块Cube matmul的内层输出tile循环。
检索词：MTE2预发、双槽、cursor、SetFlag/WaitFlag、MTE1、Mmad。
机会：aic_scalar_time明显高于aic_mac_time，且右操作数采用单槽与紧邻Set/Wait硬屏障。
代价：需要双槽资源及其生命周期、位置变换管理。
