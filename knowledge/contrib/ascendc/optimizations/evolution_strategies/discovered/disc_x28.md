---
type: Optimization
title: "X28: 小 S Prefill FA 自适应 KV Chunk 粒度"
description: "FA/GQA prefill 的 host 侧常把 kvPad = align_up(S, nChunk)，nChunk 取 cube 列分形友好的 256(fp16)/128(fp32) 大块。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.cube
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X28: 小 S Prefill FA 自适应 KV Chunk 粒度

## 核心思路
FA/GQA prefill 的 host 侧常把 `kvPad = align_up(S, nChunk)`，nChunk 取 cube 列分形友好的 256(fp16)/128(fp32) 大块。
当序列长度 S 远小于 nChunk 时，kvPad 被大幅上取整（如 S=3 → kvPad=256，绝大多数列是填充），attention 的
QK^T/softmax/PV 全在 mask 覆盖的 pad 列上白算（mask 只是让 exp→0，计算照跑）。

本策略把 nChunk 改为 **按 S 自适应**：小 S（如 S<=256）用 nChunk=64（kvPad=align_up(S,64)），kernel 支持
尾块 partial chunk（QK^T/PV 的 nCols/nKv < nChunk/KS）。对齐粒度只需 cube 列分形 16 元素，无需 256/128。

## 适用场景
- 算子：FA/GQA/MHA **prefill**（S 变化范围大，含大量小 S case）；host 以 nChunk 做序列 padding。
- 瓶颈：小 case 的 **padding 冗余计算**（over-padding on KV/sequence dim），非带宽/计算真瓶颈。
- 硬件：Ascend 910B 系列（dav-c220-vec），cube 列分形 16 对齐即可。

## 实现要点
- host 侧：`nChunk = min(256/128, kvPad)` 或按 S 阈值切换（S<=256 → nChunk=64），`kvPad = align_up(S, nChunk)`。
- kernel 侧：QK^T/PV 的 chunk 循环改为 while + 尾块 partial（nCols/nKv < nChunk 单独 Mmad/fixpipe），
  DoQKStep/AllocL0BKT/AllocL0BV 增补列宽/行宽参数。
- fp32 3xTF32 路径同步支持尾块（zZ→nZ transpose load 列宽参数化）。
- 尾块 nCols 必须 16 对齐（kvPad=align_up(S,16) 保证）。
- 联动：packDataElems 变小使更多 case 落入 host 打包融合路径；但中型 case strided-DMA pack 可能反而慢，
  需按数据量调 pack 路径阈值。

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；全量精度门禁加逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带；尾块路径需覆盖 S 小于/等于/大于 nChunk 的边界。
