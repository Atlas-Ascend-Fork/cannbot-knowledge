---
type: Optimization
title: "X54: (q, head-block) 任务切分 + 全宽 per-head 归约（消除归约指令爆炸）+ 双缓冲 tile gather + PV 行树归约"
description: "Batch MLA PagedAttention decode（nope/kpe split-KV）基线实现工作项为 (q, 全部 H head)，存在并行度不足、QK^T 按 chunk 归约导致 ReduceSum 调用数随 H×nDc 爆炸、accO/qNopeF 挤占 UB 等结构缺陷。用 (q, head-block) 任务切分先铺满核，再以全宽 per-head 归约、PV 行树归约、双缓冲 tile gather 和同步最小化降低归约与同步开销。"
tags:
  - task.optimization
  - topic.attention
  - topic.compute.reduction
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X54: (q, head-block) 任务切分 + 全宽 per-head 归约（消除归约指令爆炸）+ 双缓冲 tile gather + PV 行树归约

## 核心思路
Batch MLA PagedAttention decode（nope/kpe split-KV）基线实现工作项 = (q, 全部 H head)，对**大 H 长 KV** case 有三个结构缺陷：
1. **并行度不足**：任务数 = totalQ；totalQ 小于 AIV 核数时，大量 AIV 核闲置。
2. **归约指令爆炸**：QK^T 按 64 宽 chunk 归约，per tile 的 ReduceSum 调用数 = H×nDc，且每 chunk 一次 PipeBarrier<PIPE_ALL>，同步空泡巨大。
3. **UB 被 accO/qNopeF 占满**：H 与 Dc 大时两者各占大块 UB → T_ 被压缩。

两个正交杠杆消除上述瓶颈：
1. **(q, head-block) 任务切分**：head 维切 nHb 块，任务数 = totalQ×nHb。host 按 AIV 核数选 hb（**先用尽核，再少 KV 重读**），使任务数铺满全部核。
2. **全宽 per-head 归约**：连续 DMA 拉 [Tn,Dc]/[Tn,Dr] 整块，每 head 对 nope/kpe 各 1 次 ReduceSum → [Tn]。ReduceSum 调用数 = 2H/tile（原 H×nDc/tile）。

配套：**PV 全宽行树归约**（e 广播→[Tn,Dc] 积→对半行树归约，log2 级）+ **双缓冲 tile gather**（连续 DMA 预取下一 tile MTE2 与当前 tile 计算 V 重叠，消除内存延迟暴露，H=1 大 KV case 关键）+ **同步最小化**（每 tile 仅 1 次 PipeBarrier<PIPE_ALL>）。

## 适用场景
- decode 场景 Batch MLA / PagedAttention（nope/kpe split-KV、大 H 长 KV）向量内核
- 并行度不足 case（totalQ×H < AIV 核数，任务数=totalQ 导致欠核）→ head-block 切分填核
- QK^T 归约指令爆炸（按 64 宽 chunk 归约，ReduceSum 调用数 = H×nDc/tile）
- KV tile gather 内存延迟暴露（H=1 大 KV case）→ 双缓冲 tile gather

## 实现要点
1. host 搜索 (hb, T_)：T_∈{128..4}，hb∈{H..1}（nHb≤8），先铺满核再少 KV 重读，UB≤172KB。
2. 全宽归约：连续 DMA 整块拉取 + 每 head 单次 ReduceSum({Tn,Dc})/ReduceSum({Tn,Dr}) → [Tn]。
3. 双缓冲 tile gather：MTE2 预取下一 tile 与 V 计算重叠，消除 GM 延迟暴露。
4. PV 行树归约：e 广播 [Tn,Dc] 积 → 对半行树 ReduceSum（log2 级），累加 accO。
5. 同步最小化：每 tile 仅 1 次 PipeBarrier<PIPE_ALL>，向量同管 RAW 由硬件处理。

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
