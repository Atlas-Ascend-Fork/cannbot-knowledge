---
type: Optimization
title: "X36: Zero-Host-Padding AIV Small-Matmul（消除 host 零填充的 Vector 精确小 matmul）"
description: "matmul 系算子在 host 侧常把 M/N/K 零填充到 Cube 对齐粒度，constant_pad_nd 会发射独立的 pad kernel，其时间被计入算子总时长。对小 shape，pad kernel 可能完全主导评测指标；改为 host 不下发 pad、由 AIV 精确计算原始 shape，并做 32B 对齐行展开与多核切分，可消除该固定开销。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.tiling
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X36: Zero-Host-Padding AIV Small-Matmul（消除 host 零填充的 Vector 精确小 matmul）

## 核心思路
matmul 系算子在 host 侧常把 M/N/K 零填充到 Cube 对齐粒度（如 16），`constant_pad_nd` 会发射独立的 pad kernel（2 个），其时间被计入算子总时长。对小 shape（如 [1,2,4]→[16,16,16]），pad kernel 可能完全主导指标——此时优化 kernel 本身（MatmulImpl 初始化、mmad 时序）对总时长无济于事。

本策略：
1. **host 不 pad，直接下发原始 (B,M,K)/(B,K,N)**，彻底消除 pad kernel；
2. **AIV 核内精确计算** C[m][n] = Σ_k A[m][k]·B[k][n]，全程 fp32 累加（fp16/bf16 输入先向量 Cast 到 fp32，输出 CAST_ROUND/CAST_RINT 回 T）；
3. **32B 对齐行展开**：B/A 在 UB 中按 32B 对齐 row stride 展开（DataCopyPad 逐行零填充），使 Muls/Add/Cast 全部满足对齐与 count 约束；
4. **多核切分**：host 按 batch × M 行切分（blockDim = batch × mChunks），摊薄 AIV launch 地板；
5. **紧凑 VectorTiling**（几个 int，不含 TCubeTiling 的 ~104 int），降低 LoadTilingFromGM 开销。

## 适用场景
- matmul 系算子的**非 16 对齐小 shape**（M,N,K ≤ 64，M*K ≤ 256）：[1,2,4]、[1,8,16]、[3,6,12] 等，且评测将 host pad kernel 计入总时长
- 纯 Cube / MatmulImpl 路径对 tiny shape 的 init/launch 地板明显，AIV 精确路径可更低
- 与 X13（双引擎分流）互补：X13 在 M 阈值路由，本策略强调消除 pad + AIV 精确计算

## 实现要点
1. **准入判据 M*K ≤ 256**：AIV 标量读 UB（GetValue）是硬约束，超阈值则回退 Cube MatmulImpl
2. B/A 行展开时 `dstStride` 单位 = 32B DataBlock，`rightPadding` 单位 = 元素；对齐行（N*sizeof(T)%32==0）退化为单块 DataCopy
3. fp16→fp32 用 `CAST_ROUND`，bf32→bf16 用 `CAST_RINT`（fp32 输入跳过 cast）
4. A/B 先 Cast 到 fp32 缓冲，热循环只做 fp32 Muls/Add（规避 AIV 后端 bf16 标量→fp32 转的编译错误）
5. 全部 M 行结果先累积到 UB 缓冲（M*brow fp32），一次 barrier 后统一写回
6. 精度阈值需按 dtype 单独配（fp32 atol=1e-3；fp16 atol=9e-2；bf16 atol=1e-1）

## 验证方法
- **同设备 A/B**：固定小 shape 集合与 dtype，对比 host-pad + Cube 路径与零填充 + AIV 精确路径的端到端时间，取多次 warmup 后的中位数；确认 pad kernel 已从时间线消失。
- **全量精度**：覆盖全部小 shape、非对齐 M/N/K、非连续输入；逐元素与参考 matmul 比对，按 dtype 使用对应 atol。
- **容量审计**：核算 UB 行展开缓冲（M*brow fp32）、32B 对齐 row stride 与 M*K 准入阈值，确认不越界且多核切分覆盖全部输出。
