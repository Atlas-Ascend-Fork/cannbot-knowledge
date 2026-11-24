---
type: Optimization
title: 大末维按块累积 softmax 后逐行 topK
description: 放弃整行一次性 softmax+topK，改为末维分块累积 softmax 后逐行 topK。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/col-block-online-softmax.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：大末维按块累积 softmax 后逐行 topK

单一优化点：当输入末维（待归约维 E）很大、且 topK 的 k 也很大时，放弃「整行一次性 softmax+topK」，改为「逐行处理 + 末维按固定块切分、跨块累积 online softmax，累积完成后再做 topK」。

## 1. 原理

整行一次性处理时，on-chip cache 容量按「行数 × Ealign × 多个 buffer」计费；E 大时每批只能容下 1~2 行，外层循环次数 ≈ 总行数，单次 softmax+topK 又随 E 增长，延迟爆炸。

改为 online（流式）softmax：外层逐行，内层把 E 切成固定块（块大小与 E 解耦，取 on-chip cache 友好的值）。每读入一块就累积该行的 running-max 与 running-sum；所有块累积完毕后做一次归一化得到该行 softmax，再在其上 topK。每批 on-chip cache 占用只与「块大小」相关，与 E 无关，E 很大时仍能高效。

跨块累积的数值稳定公式（online softmax）：
- 新 max = max(old_max, block_max)
- 缩放因子 = exp(old_max − new_max)
- 累积 sum = old_sum × 缩放因子 + block_exp_sum（block 元素 exp(x − new_max) 之和）
- 最终归一化 = exp(x − final_max) / final_sum

## 2. 性能问题模式

- 输入二维 [rows, E] 或三维 [B, rows, E]，E 大（数百 ~ 上千），k 大（数十 ~ 上百）。
- 现状：每批行数受 on-chip cache 限制退化为 1~2，外层循环次数 ≈ 总行数；整行 softmax+topK 单次开销随 E 线性增长 → 大 E/大 k case 延迟数十倍于目标性能。
- 形状越往「大 E + 大 k」偏，gap 越大。

## 3. 正确性红线

- **online softmax 跨块修正**：每次更新 running-max 时，必须用 exp(old_max − new_max) 修正已累积的 sum，否则数值错误。
- **padded 列掩码**：E 对齐到块（Ealign）后，[E, Ealign) 的填充列在 softmax 归一化后必须掩成 -1（或极小值），保证不出现在 topK 结果。
- **bf16 路径**：先 cast 到 float 做 softmax 累积与 topK，结果再 cast 回原 dtype；cast 须按 Ealign stride 布局一致。
- **输出**：topK 值同输入 dtype；专家索引 / 行位置索引为 int32；行位置索引 = 行号 + j × 总行数。
- **finished 哨兵**：带 finished 的行须走单独分支（finished 行不参与正常 topK 选取）。
- **同步**：块间累积存在 producer/consumer 依赖，须在归一化、cast、topK 之间插入必要的 pipe barrier / 事件同步。

## 4. 泛化条件

- **适用**：E 大（整行入 on-chip cache 不划算）且/或 k 大；典型 E ≥ 数百 或 k ≥ 16。
- **不适用**：E 小（如 ≤ 64）且 k 小（如 ≤ 8）——此时整行处理 + 用位掩码提取选 topK 更优（见配套策略）。
- **不适用**：E 本身小于一个块，无分块必要。

## 5. 实施步骤

1. host tiling：取块大小 blockCol（on-chip cache 友好，如 64 元素量级，且为对齐因子的倍数）；ubLoop = ceil(E / blockCol)；每核分得若干行（逐行处理，行间天然并行）。
2. kernel 主循环：外层逐行 → 内层 for ubIdx in ubLoop：CopyIn 该行第 ubIdx 块 → 更新 running-max/sum（online 累积）。
3. 全块累积完成后：归一化得该行 softmax → 对 [E, Ealign) 填充列掩 -1 → 在该行 softmax 上做 topK(k) → CopyOut 值与索引。
4. bf16：块内 cast bf16→float 累积；topK 在 float 上做；结果 cast 回 bf16。
5. 行位置索引：ArithProgression 生成基序列 + 按行偏移扇出。
6. on-chip cache 预算：按「单行 + 单块」反推可同时驻留的行数，尽量用满（见配套策略）。

## 6. LLM 前置问题

- 末维 E、k 的取值范围？Ealign 对齐到多少？是否 bf16/fp16/fp32？是否有 finished？
- 当前每批处理行数 / 外层循环次数是多少？整行一次性处理还是已分块？
- topK 当前用高层 API 还是手写？k 与 E 的相对大小？

## 7. 验收标准

- build 通过 + 全部 case 精度通过（topK 值与基准一致；索引顺序敏感的输出按 case 集约定是否比对）。
- 大 E / 大 k case 延迟显著下降，向目标性能靠拢；整体均值达到目标比例。

## 检索卡（短卡）

动作：放弃整行一次性 softmax+topK，改为末维分块累积 softmax 后逐行 topK。
适用：E 大、整行装入片上缓存不划算，或 k 大；典型为 E≥数百或 k≥16。
限制：跨块更新 running-max 时，须以 exp(old_max−new_max) 修正累计和。
范围：二维[rows,E]或三维[B,rows,E]的末维归约。
检索词：online softmax、running-max、blockCol、ubLoop、topK
机会：E 大导致每批仅容纳1～2行，外层循环接近总行数。
代价：E≤64且 k≤8等小 E、小 k 情形不适用。
