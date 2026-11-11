---
type: Optimization
title: "X180: CV 环 attention 的容量/链路负结果清单"
description: "在 CV 环 attention 调优中，以下方向已被系统证伪，除非硬件或数据契约改变，不要重复投入：超出 UB/L1 容量的更大 BLOCK_N；仅摊薄 outer 事件的 KV tile 配对；chunk 级 S 流式（破坏连续 DMA fastpath）；非 2 的幂 RING/PRELAUNCH；已经隐藏的 AIV 侧开销微优化。每项都应先用容量审计和敏感性探针估上限。"
tags:
  - task.optimization
  - task.debugging
  - topic.memory
status: draft
sources: []
created_at: "2026-11-02T16:31:31Z"
updated_at: "2026-11-02T17:16:09Z"
platforms:
  - a2
  - a3
---
# X180: CV 环 attention 的容量/链路负结果清单

## 适用场景
CV 环 attention 选型/排期时，用于避免重复已证伪的容量与链路方向。

## 背景
CV 环 attention（AIC 出 S/P，AIV 做 softmax/rescale，经 GM workspace 交接）在做到一定程度后，很多"看起来合理"的方向已经被系统证伪。下面按机制归类，避免重复投入。每项都应在目标硬件/数据契约下重新评估；这里给的是**失效原因**，不是永久禁令。

## 负结果
1. **超出容量的更大 BLOCK_N**：UB 需要同时容纳 `acc_s`、`acc_s_half`、mask scratch、`m_i_2d` 等；BLOCK_N 增大后总计可能超过 UB 容量。L1 的 K/V 双槽也会恰好占满，零余量；运行时可能直接报 aicore 错误。此外 `n_chunks = BLOCK_N/128` 会让 per-chunk 的 mma/fill/FIX per score 不变，只摊薄 outer 事件，收益有限。**先做 UB/L1 预算审计，再 build。**
2. **仅摊薄 outer 事件的 KV tile 配对**：把两个 KV tile 配对到一次 ring 迭代，只能省少量跨核 handshake；敏感性探针（每 tile 插入自配对 flag）若显示标量是依赖等待，则该方向的上限很低。代价却是 S/P workspace ×2、pair 化 n2_mg、s_pp 奇偶、PRELAUNCH/尾块复杂度。
3. **chunk 级 S 流式**：把 S 的交付拆到 chunk 级，读/写会退化成 strided `DataCopyPad`（pitch 变小），丢掉整 tile 连续 DMA 的 fastpath；每 chunk 指令数翻倍、向量长度减半，FIX/向量重叠收益盖不住。
4. **非 2 的幂 RING/PRELAUNCH**：加深不解决依赖链；非 2 的幂还会在热循环里引入 modulo 标量开销。保留 2 的幂配置，除非有独立证据。
5. **AIV 侧削开销**：若 AIV 已被隐藏，删整条 P 生产链（Muls+mask+Exp）或删 l 链的收益都很小；不要再做 AIV flag 微优化。
6. **Triton q-pair 参考**：2×64 行共享 K/V 并不能超过 128 行 block 的 K/V 复用；L0C 预算也不允许 256 行。跨实现比较时要用同口径、同 case。

## 适用边界
- 以上针对 A2/DAV2201 的 CV 环 attention；换硬件（例如更新架构、regbase）或换成非 GM-workspace 交接的架构时，容量/链路结论需要重新评估。
- 若后续发现新的机制（例如 L0C→UB 通路、AIV 读 L1），这些容量/链路结论可能失效。

## 验证方法
- 每个方向先做容量审计（UB/L1/L0C/GM 足迹）与敏感性探针，再决定是否实现完整版本。
- 同设备 A/B（正反序至少 2 轮）+ 输出逐 bit / 全量精度。
- 对"看似该有效"的改动，先问：它是否同时缩短了两条并行链？如果只动一条，预期上限可能很低（见 X146/X176）。

## 关联
- 与 [X176](disc_x176.md)（scalar 等待判定）、[X149](disc_x149.md)（block_m 取满 L0C）、[X173](disc_x173.md)（head-major）配合。
