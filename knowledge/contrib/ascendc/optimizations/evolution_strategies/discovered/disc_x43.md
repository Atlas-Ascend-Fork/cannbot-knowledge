---
type: Optimization
title: "X43: Cube 输出 FixPipe 融合 Epilogue（C_TYPE=输出 dtype + SetBias，acc 不落 GM）"
description: "Matmul 流水最后一段是 L0C → FixPipe → GM 的输出通路；将独立 epilogue（bias-add/cast/requant）下沉进 FixPipe：C_TYPE 设为输出 dtype 并 EnableBias/SetBias，使 fp32 acc 不落 GM，消除 epilogue kernel launch 与 acc 的 GM 往返。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.quantization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X43: Cube 输出 FixPipe 融合 Epilogue（C_TYPE=输出 dtype + SetBias，acc 不落 GM）

## 核心思路
Matmul 流水最后一段是 L0C → FixPipe → GM 的输出通路。把独立 epilogue kernel（bias-add +
cast + requant）下沉进 cube 的 FixPipe 阶段：**C_TYPE 直接设为输出 dtype（fp16/bf16）**，
`EnableBias` + `SetBias` 在 FixPipe 内做 fp32 acc + bias 后再 F322F16/F322BF16 写回 GM。
效果：**acc fp32 [M,N] 完全不落 GM**，消除 epilogue kernel launch（launch 数 -1）+ acc 的
GM 写/读往返。对 dequant→matmul→epilogue 的串行流水是第一个结构性消除点。

## 适用场景
- matmul + 向量后处理（bias/cast/轻量 elementwise）的 CV 融合算子，后处理不含跨行归约
- 独立 epilogue kernel 占 kernel 时间显著（小/中 shape 尤其明显，launch + GM 往返开销大）
- 输出 dtype 与 L0C acc dtype 不同的算子（fp32 acc → fp16/bf16 输出，最典型）

## 实现要点
1. **C_TYPE = 输出 dtype + EnableBias(hasBias)**：quantMode==0（无 requant）路径。C_TYPE
   从 fp32 改为输出 dtype，FixPipe 在 L0C fp32 上自动加 bias 并 cast 后写 GM。
2. **SetBias 必须 per-N-tile 全局列偏移**：`mm.SetBias(biasGlobal[nIdx*singleN])` —— Matmul
   内置 bias 的基址偏移只按核内 fragment 索引计算，grid-stride 切分下不自动按 nIdx 列块
   偏移，否则多 N-tile 时 bias 加错列（表现为输出偏差）。
3. **一个 ascendc_library 只能放一个 MIX cube kernel**：融合入口需放独立 ascendc_library，
   否则同库多 MIX 入口导致 kernel 注册被破坏（输出全零）。
4. **保留 quantMode>=1 fallback**：requant 场景仍走 fp32 acc + 独立 epilogue（round 语义
   clamp 不适合 FixPipe 单指令表达）。
5. **互斥检查**：与 Split-K 互斥——fp16/bf16 输出 C 上 enAtomic GM 原子累加会损坏结果；
   有 Split-K 需求时需改回 fp32 acc + 独立 epilogue。
6. **与 dequant 融合叠加**：可与 AIV producer/AIC consumer 或 SyncAll 单 MIX kernel
   叠加，把多 kernel 压到单 kernel；SyncAll 全 barrier 会使 dequant→matmul 仍串行，
   需评估流水重叠。

## 验证方法
- **同设备 A/B 对比**：固定设备型号、CANN 版本、输入 shape 与 dtype，优化前后各跑多轮（含 warmup），取 kernel Duration 中位数对比；不跨设备或跨版本混合测量。
- **全精度校验**：用 PyTorch/参考实现逐元素比对，覆盖 fp32 acc → fp16/bf16 输出与带/不带 bias 路径，满足对应 dtype 的 rtol/atol，且无 NaN/Inf。
- **容量审计**：核算 L0C/L1/UB 占用与 FixPipe 输出缓冲需求，确认融合后在容量内；检查 32B 对齐、16×16 fractal 与多 N-tile 的列偏移边界。
