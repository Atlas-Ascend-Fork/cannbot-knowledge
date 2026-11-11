---
type: Optimization
title: "X22: Depthwise 直接卷积（绕过 im2col+GEMM）"
description: "depthwise（groups==Cin, cig==1）卷积在 im2col+GEMM 流水线中极低效：GEMM 退化为 M×Kpad @ Kpad×1 逐通道点积，fp16 hi/lo 分裂使 Cube 工作量约 3 倍，且 4 阶段流水线物化 4 个 GM workspace。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.neighborhood.convolution
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X22: Depthwise 直接卷积（绕过 im2col+GEMM）

## 核心思路
depthwise（groups==Cin, cig==1）卷积在 im2col+GEMM 流水线中极低效：GEMM 退化为 M×Kpad @ Kpad×1 逐通道点积，fp16 hi/lo 分裂使 Cube 工作量约 3 倍，且 4 阶段流水线物化 4 个 GM workspace。X22 用**单 AIV fp32 向量卷积内核**直接计算逐通道 kh*kw dot product：无 im2col、无 GEMM、无 fp16 分裂、无 GM workspace、无 Cube。

## 适用场景
- **算子类型**: depthwise 卷积（groups==Cin, cig==1），且 sW==1、Wo>=8、W>=8、Co%8==0、Co>=8 时收益最大
- **瓶颈类型**: im2col 标量 gather、GM workspace 物化、Cube 利用率极低（GEMM M×1）

## 实现要点
1. **Tile = (image, co-block=8, oh-block)**：co-block 8 使 NMC [B,M,Co] 输出 32B 对齐（blockLen=8*4B）；acc 按 co-major [8][plane] 计算，UB 内 transpose 到 [m][8]，一次 2D DataCopyPad 存储（dstStride=(Co-8)*4）
2. **对齐 interior + 标量 head/tail 分离**：32B 对齐 interior 用向量 Muls/Add（per-tap 对齐 tapBuf 从 GM DataCopyPad 加载）；<=7 elems 的 head/tail 写入独立 corr 缓冲（scalar S-pipe），oh-block 末尾一次向量 Add 并入——消除 acc 的 S/V hazard，热循环只需 MTE2_S/MTE2_V/V_MTE2 事件等待
3. **fp32 精确累加**（满足紧容差精度要求）
4. **平台坑**: `PipeBarrier<PIPE_S>` 在 910B2C 崩溃 → 用 `PipeBarrier<PIPE_ALL>`；DataCopyPad UB 目标必须 32B 对齐（weight 缓冲按 RUp8(kH*kW) 步长）；corr 清零需覆盖完整 plane
5. **Host 门控**: cig==1 && sW==1 && Wo>=8 && W>=8 && Co%8==0 && Co>=8 走 fused 内核，其余回退通用流水线

## Grouped 推广
把 depthwise 直接卷积推广到 general grouped conv（groups>1, cig∈[4,8]）：同一 group 的 8 个输出通道块共享 CiG 输入行，
**CiG 通道维 2D DataCopyPad burst**（srcStride=H*W-W, 一条 MTE2 事务取全部 CiG 行）消 undersize transfer；
kW tap burst 合并到一条 MTE2_V 等待、FMA 合并到一条 V_MTE2 等待。
关键门控：W%8==0（sub-32B DataCopyPad 在 910B2C 崩溃）、cog%8==0、Co%8==0、Wo%8==0、cig*kk<=128。

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；全量精度门禁加逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
