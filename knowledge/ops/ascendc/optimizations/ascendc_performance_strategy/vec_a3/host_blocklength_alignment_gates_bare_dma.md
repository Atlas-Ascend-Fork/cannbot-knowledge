---
type: Optimization
title: host 侧 blockLength 32 元素对齐扩大裸 DMA 覆盖（大 case 分档）
description: host将blockLength向上对齐到32元素，使对齐分支采用裸DataCopy而非DataCopyPad
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-host-blocklength-alignment-gates-bare-dma.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：host 侧 blockLength 32 元素对齐扩大裸 DMA 覆盖（大 case 分档）

> 单一优化点：多核均分时 host 把 blockLength 向上对齐到 32 元素，使每核 GM base 偏移对任何 1B/2B/4B dtype 都 32B 对齐，kernel 内既有"对齐走裸 DataCopy"分支的全 tile 与多数 tail 自动生效；对齐仅对大工作集（≥4M 元素）启用。

## 1. 原理
裸 DataCopy 比 DataCopyPad 少填充逻辑与同步开销。每核起点 blockIdx*blockLength，
blockLength 是 32 倍数 ⇒ 起点字节偏移是 32 倍数（int8 亦然）。大 case（BW-bound）
tail 多、收益累积：实测 16M-67M case 改善 5-10%。

## 2. 性能问题模式
- 触发：kernel 已有对齐 fast path 但非对齐 shape（素数边）的 per-core 起点常落
  非对齐地址，整核退回 Pad 路径。
- profiling 特征：非对齐大 case 与对齐大 case 单位字节耗时差异明显。
- 不适用：~1M 小 case——对齐移动尾核块边界，实测退化 12-15%（须分档关闭）；
  blockLength 已自然对齐的 shape（收益为零）。

## 3. 正确性红线
- kernel 侧 per-core 长度必须 clamp（curLen = min(blockLen, total-coreStart)），
  否则对齐多出的尾巴越界；
- 对齐只在 host 改，kernel 判断（coreStart*elemSize % 32）自动受益，无需双改。

## 4. 泛化条件
- **适用**：任何 contiguous 均分多核 + kernel 内对齐分派两路 DMA 的实现。
- **不适用**：非 contiguous 切分（按行/按段）场景需另行推导对齐粒度。

## 5. 实施步骤
1. host tiling：`blockLength = (blockLength+31)/32*32;`（按 totalLength 阈值分档）；
2. 确认 kernel per-core clamp 语义；
3. 回归：小 case（<阈值）必须逐位持平（未改动路径）。

## 6. LLM 前置问题
- 非对齐小 case 退化的分档阈值怎么选？（本例 4M 由 20 case 网格二分得到，换硬件/算子需重标。）
- kernel 侧 per-core clamp 语义是否已存在，能否保证对齐多出的尾巴不越界？
- 目标 shape 的 blockLength 是否已自然对齐（收益为零的情形）？

## 7. 验收标准
- build 通过，全量精度回归通过；小 case（<分档阈值）逐位持平（未改动路径）。
- 卡内实测达标：大 case（16M-67M 元素）改善 5-10%；~1M 小 case 无退化（分档关闭生效）。
- kernel 侧 clamp（curLen = min(blockLen, total-coreStart)）确认存在，无越界。

## 检索卡（短卡）

动作：host将blockLength向上对齐到32元素，使对齐分支采用裸DataCopy而非DataCopyPad
适用：contiguous均分多核，且kernel按对齐状态分派两路DMA
限制：每核长度必须clamp；非contiguous按行/段切分不能直接套用
范围：host多核均分tiling与kernel每核DMA入口
检索词：blockLength、32元素对齐、per-core、DataCopy、DataCopyPad、GM偏移
机会：已有对齐fast path，但非对齐shape使每核起点失配并整核退回Pad路径
