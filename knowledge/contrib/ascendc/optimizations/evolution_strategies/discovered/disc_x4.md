---
type: Optimization
title: "X4: Concat-Fused Strided DMA + Two-Level Skv Reduction"
description: "decode/MTP attention（单行/小批量 Q、长 Skv）受 DMA launch latency/per-key 同步支配时，把 concat 折叠进 K-tile DMA、Skv 用两级向量归约、online softmax 单遍化，把 per-key DMA/sync 从 O(Skv) 降到 O(tiles)。"
tags:
  - task.optimization
  - topic.attention
  - topic.compute.normalization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/discovered/disc_X4.md
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T15:50:00Z"
platforms:
  - a2
---
# Strategy X4: Concat-Fused Strided DMA + Two-Level Skv Reduction

## 核心思路
针对 decode/MTP attention（单行/小批量 Q、长 Skv）的 **DMA-launch-latency-bound** 瓶颈（非 BW）：
1. **Concat 折叠进 K-tile DMA**：一个 tile 用两条 MTE2（nope-tile / rope-tile）以 strided dst 交错写入连续 `[T,D_qk]` UB（ND2NZ 式 packed load）。N_kv=1 时两个 burst 背靠背=一次物理传输，host 侧 `torch.cat` / 逐 key 双 DMA 消失。
2. **Skv sweep 两级向量归约**：`vmul(q,k) -> vcadd -> vcadd` 把每个 dot 直接写进 `score[r]`，去掉逐 key 标量部分和、逐 key DMA、逐 key sync。
3. **单遍 FlashAttention-2 online softmax**：同 tile 的 V 重叠加载并在同遍累加到 fp32 `o_f`，4 遍 -> 1 遍；标量 exp 用 1-lane `vexp`（不依赖 libm）。

本质是把 decode 的 per-key DMA/sync 从 O(Skv) 降到 O(tiles)，直击 launch-latency 项；fp32 online-softmax 与 2-pass 代数等价，精度不损。

## 适用场景
- 算子：decode/MTP 阶段 attention（单行/小批量 Q、长 KV 序列、GQA N_kv=1 尤佳；concat 型 Q/K，如 MLA 的 nope+rope）。
- 瓶颈：DMA launch latency / per-key sync 主导（大量短 MTE2 + 高同步频率），而非 BW 或 compute。
- 硬件：Ascend A2 系列 vector 核（dav-c220-vec），UB 放得下 K-tile+V-tile+fp32 状态（tile<=64 @fp16 约 150KB / 192KB）。

## 实现要点
- K-tile 用两条带 strided dst 的 MTE2 拼 nope+rope，dst stride 按 D_qk 交错，保证 32B 对齐。
- dot 用 `vmul->vcadd->vcadd` 两级归约直接落 `score[r]`，禁用逐 key 标量累加。
- online softmax：fp32 m/l/o 驻留 UB 跨 tile rescale（`o_f *= exp(m_old - m_new)`），exp 用 1-lane `vexp`；同 tile V 与 score 重叠加载。
- 多 repeat 的 `vmul/vcadd/vaxpy` 间存在 RAW 依赖，`pipe_barrier(PIPE_V)` 不可省（删除 barrier 会导致精度问题）。

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
