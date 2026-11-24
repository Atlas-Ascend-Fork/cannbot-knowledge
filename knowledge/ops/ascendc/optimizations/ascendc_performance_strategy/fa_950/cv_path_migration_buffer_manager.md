---
type: Optimization
title: 11 - CV 通路迁移：BufferManager 模式（arch35 对齐）
description: 以BufferManager模式迁移CV通路，打通AIC↔AIV的UB→L1直通。
tags:
- task.optimization
- topic.attention
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/11-cv-path-migration-buffer-manager.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 11 - CV 通路迁移：BufferManager 模式（arch35 对齐）

## 适用条件

- A5 (Ascend950/arch35/dav-3510)，SFA 类稀疏 attention（cube Mmad + vec gather/softmax）。
- 目标：打通 AIC↔AIV 的 UB→L1 直通，省 K_sel/V_sel 的 GM 一写一读（两段式 workspace 中转）。
- 硬件前提（arch35 参考实现 `ai_infra_sparse_flash_attention_pioneer/op_kernel/arch35/` 已实证）：
  - 编译选项 `ENABLE_CV_COMM_VIA_SSBUF=true`（950PR/DT 的 UB→L1 硬件通道；不开则底层仍走 GM，精度对但性能不变）。
  - L1 容量 512KB：`l1Pool = [Q | K_sel_slot0/1/2]`，full K_sel（topKBaseAlign16 × dkAlign × 3 slot）超 512KB 的 shape 必须退化两段式。

## 做法

1. **kernel 层 l1Pool_（阶段0）**：`l1Pool_` 从 cube 私有提升到 kernel 层，AIC/AIV **同序列** `pipe->InitBuffer(l1Pool_, ...)`（各自 TPipe 的第一个 A1）——破解「AIV 侧裸加 A1 InitBuffer 扰动 event ID」的分配契约问题。cube 经 `SetL1PoolView(l1Pool_.Get<QType>())` 拿视图。
2. **vec 端写入（写法 a，arch35 三步式）**：
   - `Copy(ubNz, gatherUb_, dkAlign, rows, {17,1,1,dkAlign/16})`——UB 内 ND→NZ，17-stride 防 bank 冲突（V pipe，**不是** DataCopy Nd2Nz）。
   - `SetWaitFlag<HardEvent::V_MTE3>()`——V→MTE3 RAW。
   - `DataCopyParams` UB NZ→L1（MTE3，去 padding；dstGap=topKBaseAlign16-16 → L1 C0 stride=topKBaseAlign16）。
   - `SetWaitFlag<HardEvent::MTE3_V>()`——MTE3→V WAR（单缓冲 ubNzBuf_ 跨批/跨 Gather 复用）。
3. **cube 端直读（关键参数）**：`LoadNzL1ToZnL0B(bL0, l1PoolView_[nzOff], kAlign, nRowsAlign, topKBaseAlign16_, transpose)`——第 5 参数 srcC0Stride **必须是 topKBaseAlign16_**（匹配 vec 写入的 NZ C0 stride），**不是** GM 路径 kselQueL1_ 的 nRowsAlign。这是直读 l1Pool_ 与读 kselQueL1_ 的唯一参数差异。
4. **MM1/MM2 都直读** l1Pool_ 的 K_sel 段（MM1 全 dk 列、MM2 前 Dv 列共用一份数据）。
5. **容量门控**：kernel `useL1Path_ = (totalL1BytesIfPath + 32 <= 512KB)`，超限自动退化 GM 两段式。
6. cube wait pipe 用 MTE1（LoadData L0B），不再 MTE2。

## 陷阱（前期实测教训）

- **LoadNzL1ToZnL0B 直读 l1Pool_ 若 srcC0Stride 误用 nRowsAlign → mismatch ~92%**；任何「读 l1PoolView_ 不对」的判断先核这个参数。
- **Nd2Nz 写法 b（DataCopy UB→L1 随路 Nd2Nz）在 A5 上 errcode 81 越界**——必须用三步式写法 a。
- **vec 保留双写**（GM wsKselGm + l1Pool_）：GM 写与 Copy(V) 并行互相掩盖延迟，跳过 GM 写会让 Copy(V) 裸露关键路径，prefill 大 case 回退 40~90%（实测 geomean 1.050→0.885x）。
- topKBaseSize=256/512 的 MLA shape（G 大、dk 512/576）容量超 → 自动退化，性能与 no-CV 持平（零额外开销）。

## 验证重点

- 精度：37/37（含 BSND/BNSD、fp16/bf16、GQA/MQA/MLA、topK 1~1024、非对齐/退化 case）。
- 性能：CV 开启 case（dk=128 GQA，容量 ~476KB）prefill 大 S1 收益最大（S1=1024 实测 +3.6%~+44%）；mtp 类 vec 密集 case 收益小甚至 -12%（双写开销）。
- 收益规律：收益 ∝ cube 读 GM K_sel 次数（S1 大收益大），开销 ∝ vec 双写 K_sel 量（topKBaseSize 大开销大）。

## 检索卡（短卡）

动作：以BufferManager模式迁移CV通路，打通AIC↔AIV的UB→L1直通。
适用：适用于由cube Mmad与vec gather/softmax协作的SFA类稀疏attention。
限制：目标平台限A5（Ascend950、arch35、dav-3510）。
范围：SFA类稀疏attention的cube与vec协同通路。
检索词：BufferManager、CV通路、AIC↔AIV、UB→L1、arch35。
