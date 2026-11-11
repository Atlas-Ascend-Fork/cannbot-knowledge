---
type: Optimization
title: "X5: GQA-Decode GEMV->GEMM (M=N_q)"
description: "GQA/MLA decode 或 MTP 在 N_kv=1（或 N_kv≪N_q）时，把 decode 注意力的 M 维取为 N_q 而非 S，使 QK^T 与 PV 都成为稠密 cube GEMM，替代 N_q 条独立归约型 GEMV。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.cube
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/discovered/disc_X5.md
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T15:50:00Z"
platforms:
  - a2
---
# Strategy X5: GQA-Decode GEMV->GEMM (M=N_q)

## 核心思路
对 GQA decode/MTP（N_kv=1，一个 token 的全部 N_q 个 query head 共享同一个 KV head），把 decode 注意力的 M 维取为 **N_q** 而非 S。于是一块 = 一个 (b,s) token、grid=B·S、M=N_q，QK^T 与 PV 都成为稠密 cube GEMM（M 足够大），替代 vec 路径里 N_q 条独立的归约型 GEMV。这是把 decode 从 AIV/GEMV 换到 AIC/GEMM 的**计算域切换**，由 N_kv=1 不变量保证 M=N_q 足够大以喂饱 cube。

## 适用场景
- 算子：GQA/MLA decode 或 MTP（S∈{1,2}）且 N_kv=1（或 N_kv≪N_q）。
- 不适用：prefill（S 大，已是 GEMM）、MHA（N_kv=N_q，M=N_q 但 K/V 不能 head 共享流一次）、N_kv>1 的 GQA（K/V 需按 KV head 重复，退化回多 GEMM）。

## 实现要点
- 新增 sibling decode kernel（C-V 1AIC:2AIV FFTS），prefill 路径字节不变；plugin 在 prefill 前加 `use_decode_mix=(S∈{1,2} && 对齐)` 分发。
- AIV：按 head marshal Q（layout-aware），透明 fp32 行 softmax（无 max-shift，score 为 O(1)），因果尾 mask 跨 head 一致（mask 仅依赖 s）。
- AIC：QK^T 的 K 每 token 流一次（N-chunk NC=256）；PV 做 K-tile（KC=256）+ N-tile（NV=128，使 cL0[N_q,128]=64KB≤L0C 128KB）；V 用 proven 子列 nd2nz 流一次，cube fixpipe 直接落 y（无 o_scr 往返）。
- 3 个 one-shot FFTS flag（MARSHAL/CS/VP）；EVENT_ID 使用固定的 prefill 事件 id 集合。
- Trade-off：AIC/AIV 串行（FFTS）、Q 每 NC-chunk 重载、半核轮流空闲、L0C 限 NV=128（P 重流 ndv=4×），但 cube 吞吐 + 内存最优流式主导。

## 与既有策略的关系
- X4 是最佳 VEC 骨架；P*/D*/A* 卡在单一计算域内做 tiling/buffer/vectorize。X5 改变 decode 的**计算域**（AIV→AIC、GEMV→GEMM），是结构性 reformulation，不是任何单卡的组合。

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
