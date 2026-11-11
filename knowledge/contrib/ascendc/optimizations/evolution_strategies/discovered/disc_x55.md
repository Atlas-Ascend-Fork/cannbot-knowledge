---
type: Optimization
title: "X55: Shared-im2col 双分支 Conv-on-Cube（一份 im2col 供两分支 + HF32-for-fp32 conv 路由）"
description: "融合算子含两个共享同一输入 x 的 3x3 conv 分支时，用纯 AIV kernel 构建一份 im2col 供两个分支的 fp32 Cube GEMM（transA）复用，避免重复 im2col；fp32 输入启用 HF32 匹配参考 conv2d 的 cube 舍入，fp16/bf16 走全 fp32；按 C 大小在 Cube conv 与 Vector conv 间路由。"
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

# Strategy X55: Shared-im2col 双分支 Conv-on-Cube（一份 im2col 供两分支 + HF32-for-fp32 conv 路由）

## 核心思路
融合算子含**两个共享同一输入 x 的 3x3 conv 分支**（如 Dual Attention 的位置/通道注意力分支）时：
1. **一份 im2col 矩阵供两分支复用**：纯 AIV kernel 构建一次 im2col Ic[B,9C,N]（fp32），两个分支的 conv GEMM 都读它——im2col 构建成本从 2 次摊销为 1 次。
2. **两个 fp32 Cube GEMM（transA）**：`yp = wpF^T @ Ic`、`yc = wcF^T @ Ic`（[C,N] = [C,9C] @ [9C,N]），wpF/wcF 直接用原始 [C,9,C] 权重当 [9C,C]（TRANS_A），零 host permute/repack。
3. **HF32-for-fp32 conv 路由**：fp32 输入启用 HF32（匹配 NPU 参考 conv2d 的 cube 舍入），fp16/bf16 走全 fp32（上 cast 乘积精确匹配参考）。
4. **Shape 自适应路由**：C>=128 走 Cube conv；小 C 保留已证高效的 Vector conv。

## 适用场景
- 多分支共享输入的 conv（Dual Attention / 并行 attention 结构）
- conv 是 Vector 外积累加、大 C case compute-bound 的融合算子
- 有多个 bmm/attention 已上 Cube、conv 成为剩余瓶颈的算子

## 实现要点
- im2col 布局 (B,C,9,N) 连续，K 行 = ci*9+k；权重 (ci,k,co) 行主 → transA GEMM 零 repack
- 32B 对齐：im2col 每行 slot 布局（slotElems=ceil(W*sizeof(T)/32)*32/sizeof(T)），DataCopyPad dst/src stride 按 slot
- 边界行（kh=0 的 h=0 与 kh=2 的 h=H-1）host 用 at::zeros 预清零，kernel skip 边界 task
- 9N store stride 溢出（fp16 大 N）回退 Vector conv
- HF32 仅 fp32 conv 启用（匹配参考）；bmm 恒 SetHF32(false) 全精度

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。

## 补充判据（跨算子复核）

- **同一输入被多个阶段重复 im2col 时，优先预计算部分和并复用**：让上游阶段多做一小块 GEMM（如 `acc_x = W[:, :k9c] @ bmat_x`），把结果存成 `[b, ch, hwp]`，下游阶段只 im2col 新输入并累加，比在每个阶段各做一次 im2col 更省（实测 +2.4%）。
- **边界**：需要额外 workspace，但可通过收缩 bmat 腾出空间；与 pad fold 叠加可能回退（实测 -11%），不要无条件组合。
