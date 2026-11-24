---
type: Optimization
title: 连续输出行的等差段批量 gather
description: 将快路径每行一次 DataCopy 改为对连续输出行的等差源段执行批量 gather。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-fastpath-arithmetic-segment-batch-gather.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：连续输出行的等差段批量 gather

单一优化点：transpose 类算子的「快路径」（输出行=输入内连续段，fastStride==1）CopyIn 逐行发 DataCopy 时，
利用「输出行源段在不跨内层维边界时严格等差（步进=innerSize）」的性质，改为按等差段的 strided DataCopyPad 批量搬运。

## 1. 原理
输出行 r 的源基址 baseIn(r) 由混合进制坐标解码；r 递增时最低维（perm[rank-2] 对应维）坐标 +1，
步进恒为 inStride[perm[rank-2]]——在该维不进位的段内（段长 shape[perm[rank-2]] 行）等差成立。
跨段边界时跳变 → 必须按段拆批；blockCount 上限 4095 再拆。

## 2. 性能问题模式
- 快路径逐行 DataCopy（每行 1 条 MTE 指令）× 数万行/核 + 每轮 PIPE_ALL；
- 实测 case（64,32,512,128 fp16 perm=[0,2,1,3]）1517us，改批量后 389us。

## 3. 正确性红线
- 等差仅在段内成立：整段直接算会跨段越界读（实测设备挂死 507035）；必须 min(段剩余, 4095, 行剩余) 拆批；
- 快路径去掉 PIPE_ALL 会得到错数据（TQue 双缓冲下 MTE3 与下轮 MTE2 竞争），barrier 不能省。

## 4. 泛化条件
适用：输出行源段连续（fastStride==1）但行间不背靠背（行距≠innerSize）的 gather 场景。
不适用：行距==innerSize（GM 源整体连续，直接整块拷贝）；行距不定（泛化 perm 进位密集）。

## 5. 实施步骤
1. host：srcStrideBytes=(inStride[perm[rank-2]]-innerSize)*dts；innerLoopNum=shape[perm[rank-2]]（段长）。
2. kernel：循环内按段拆批，每批 1 条 {blockCount=blocks, blockLen=inner*dts, srcStride=gap, dstStride=0}。

## 6. LLM 前置问题
- perm[rank-2] 对应维的 shape 与 inStride（段长与行距）是多少？
- baseRows（每轮行数）与段长的对齐关系？

## 7. 验收标准
- 精度不变（仍是纯 gather）；快路径 case 提速 ≥3x；其它路径不回归。

## 检索卡（短卡）

动作：将快路径每行一次 DataCopy 改为对连续输出行的等差源段执行批量 gather。
适用：适用于 fastStride==1、源段连续但行距不等于 innerSize 的 gather。
限制：等差关系仅在不进位段内成立，禁止跨段直接计算，以免越界读。
范围：transpose 类算子的 fastStride==1 快路径 CopyIn。
检索词：fastStride、DataCopy、MTE、inStride、innerSize、等差段、gather
机会：每核存在大量逐行 DataCopy，且每轮执行 PIPE_ALL。
