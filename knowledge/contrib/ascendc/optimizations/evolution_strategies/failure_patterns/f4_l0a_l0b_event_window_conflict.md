---
type: Optimization
title: 'F4: MTE1_M+M_MTE1:L0A/L0B:event_window_conflict'
description: 批量/连续 launch 时随机（大 shape 0–2 次迭代内、小 shape 40 次不现）报：
tags:
- task.debugging
- topic.data_movement
- topic.programming_model
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/4917980395de8b8703aa7ec62213fafbe7bec01e/plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/runbooks/failure-patterns/f4-l0a-l0b-event-window-conflict.md
  role: evidence
created_at: '2026-10-29T19:00:00Z'
updated_at: '2026-10-29T20:45:00Z'
platforms:
- a2
- a3
---

# F4: MTE1_M+M_MTE1:L0A/L0B:event_window_conflict

> 进化失败模式元数据（迁移自旧 OKF，机器可读副本见 ascendc-evolution-knowledge/references/okf_compat.json）：
> key: "MTE1_M+M_MTE1:L0A/L0B:event_window_conflict"
> phenomenon: runtime_failure
> severity: blocking
> failed_combination: ["MTE1_M", "M_MTE1", "L1_DRAIN=false"]
> operator_type: ["attention", "cv_fusion", "matmul"]
> occurrences: 2

## Symptom
批量/连续 launch 时随机（大 shape 0–2 次迭代内、小 shape 40 次不现）报：
`EE9999 ... error code 507015 (aicore exception)`，plog 解码为
`L0B read/write conflict in the MTE (same address)`（errcode 0x8000004000）或
`L0A read/write conflict`（errcode 0x4000000800），`mte error info` 与 `fixp_error0` 低位相同，
`blk` 随机（2/3/8/9/14/23），`blockDim=24`。同一二进制在 accuracy（单次执行）模式不现。

## Root cause class
同步事件语义 —— 在本 build（CANN 9.1.0 / 910B2C / bisheng）上，
`SetFlag/WaitFlag<HardEvent::MTE1_M>`、`<HardEvent::M_MTE1>` 以及 per-ring-slot 的
`<HardEvent::MTE2_MTE1>`（配合 `L1_DRAIN=false` 关掉 gemm_v0 入口整条 MTE2 排空）
**只覆盖指令流的发射顺序，不覆盖**：
  * MTE2 page DMA 真正落进 L1 的窗口（MTE1 随即读该页），以及
  * cube 对 L0A/L0B 的操作数读窗口。
因此下一步的 `L1→L0` store 会写进「MTE2 正在填的 L1 页 / Mmad 正在读的 L0 地址」，
MTE 检测到同地址读写即抛错并中止整个 launch。

## Failed combination
- 仅用事件握手保护 L0 ping-pong（`MTE1_M` + `M_MTE1`），且用 per-slot `MTE2_MTE1` 替代 gemm 入口 L1 排空（`L1_DRAIN=false`）
- 换事件 ID 隔离两个方向（`MTE1_M` 移到 2/3）**无效** → 不是 ID 复用问题
- 只在 Mmad 之后加排水（`PipeBarrier<PIPE_M>` / `PIPE_ALL`）**无效** → 排的是指令流不是 cube 读窗口
- 只把 `PipeBarrier<PIPE_ALL>` 换成 `PipeBarrier<PIPE_MTE2>()` **无效**

## Additional evidence (round 3)
槽位复用距离 2（L0 双槽跨调用交替）且**完全去掉 drain** 时仍会崩（case 26 与 [8,18,24,26] bundle 各 60 iter 内 507015）
⇒ cube 对 L0A/L0B 的操作数读可以落后 M 流水 >1 个 Mmad，事件与 2 步复用距离都不够。
可行折中：跨调用续接槽位 + **隔步（每 2 次 gemm 一次）** `PipeBarrier<PIPE_ALL>`，实测干净且把代价从 1.46x 降到 ~1.38x（见 X63）。

## Resolution
在 `gemm_v0` 里 `WaitFlag<M_MTE1>(pp)` 之后、`copy_l1_to_l0a/b` 之前插入
`PipeBarrier<PIPE_ALL>()`：实测 case26 60/60、mix bundle 60/60、3 次连续全量 50 例 batch 无 507015。
代价：该屏障会等待「DMA-first」刚发出的 page DMA，实测 geomean 480.55us → 716.6us（-1.49x）。
吞吐恢复两步（已验其一）：
  1. 把下一组的 page DMA 发射点移到本组 gemm 之后（QK 相位实测 781.5 → 716.6us）；
  2. PV 相位 / per-slot / fp32 路径的预取块同样后移（待验证）。

## Evidence
48_GqaSparseFwd 进化 round_1：seed v5b 在 device 0/1/3 上 case26 0–8 次迭代必现；
round_1/parallel_1 的 fix 版 3 次连续全量 50 例 quick-batch 全 50/50 有效、零 507015；
round_1/parallel_0 用未改动的 seed 二进制复现同一错误（2/2），排除候选引入。
