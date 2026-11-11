---
type: Optimization
title: "X44: fp32 Cube mmad 全量重写替代向量模拟 matmul（SetHF32(false) 全精度）"
description: "若内核用 AIV 向量标量模拟 matmul（16×16 tile 逐点 GetValue 累加），会完全绕过 Cube 矩阵单元，成为数量级性能瓶颈；改用 Matmul 高阶 API 走 fp32 Cube，并用 SetHF32(false) 关闭 HF32 截断获得全精度。"
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

# Strategy X44: fp32 Cube mmad 全量重写替代向量模拟 matmul（SetHF32(false) 全精度）

## 核心思路
若内核用 AIV 向量标量模拟 matmul（16×16 tile 逐点 GetValue 累加），会完全绕过 Cube 矩阵
单元，是数量级性能杀手。把算子内全部 matmul（attention 的 QK^T/PV/W_o）改用 Matmul
高阶 API（`ASCENDC_CUBE_ONLY` + `REGIST_MATMUL_OBJ` + `IterateAll`）直接走 fp32 Cube；
在目标 Ascend 平台上 `SetHF32(false)` 关闭 HF32 精度截断获得全精度。

## 适用场景
- 任何 matmul 被实现为向量标量模拟（AIV GetValue 逐点累加）的算子
- attention 族多 matmul 流水（QK^T→softmax→PV→W_o），fp32 精度路径不再需 fp16
  hi/lo 拆分（HF32 拆分的多次 gemm 被 SetHF32(false) 全精度单次 gemm 取代）
- 小/中 shape 为主、gemm 非瓶颈上限的算子：全精度比 HF32 慢但 shape 小可接受

## 实现要点
1. `SetHF32(false)` 全精度：HF32 仅 10-bit 尾数，不够 fp32 精度要求；关闭后满足 fp32
   精度校验。
2. Matmul 高阶 API：`ASCENDC_CUBE_ONLY` + `REGIST_MATMUL_OBJ` + `IterateAll`，AIC 执行。
3. fp32 向量 op count 必须 ≥8 且为 8 的倍数；手写 halving 归约在 nPad 非 2 幂时越界，
   改用 WholeReduceMax/Sum。
4. uint8 位图 mask 向量操作必须 256-bit block 对齐（count 是 256 的倍数），否则 mask
   写入不完整 → softmax 输出退化为均匀分布。
5. 小 seqLen 统一 sR16=max(64, ceil(S/16)*16)，防 mask 对齐问题。
6. exp 必须保留行 max 减法防下溢 → NaN。

## 验证方法
- **同设备 A/B 对比**：固定设备型号、CANN 版本、输入 shape 与 dtype，优化前后各跑多轮（含 warmup），取 kernel Duration 中位数对比；不跨设备或跨版本混合测量。
- **全精度校验**：用 PyTorch/参考实现逐元素比对，覆盖 fp32/bf16/fp16 与 mask/边界 seqLen，满足对应 dtype 的 rtol/atol，且无 NaN/Inf。
- **容量审计**：核算 L0C/L1/UB 占用与向量临时缓冲需求，确认 16×16 fractal、256-bit block 对齐与 sR16 padding 在容量内。

## 补充判据（跨算子复核）

- **AIV 标量吞吐约为 Cube 的 1/30–40**：按名义 FLOP 占比估算会严重低估 AIV 标量模拟的时间占比；判断是否 Cube 化应看 profiling 的时间占比（AIV vector/scalar busy vs cube），而不是看 attention FLOP 只占几个百分点。
- **精度契约**：fp32 参考全链路时，不要用 fp16/bf16 原生计算换 Cube 吞吐；Cube 化的前提是保持 fp32 精度契约（或按参考的舍入规则做等价载体）。
