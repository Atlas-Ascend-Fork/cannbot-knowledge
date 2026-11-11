---
type: Optimization
title: "X14: Mix-Kernel 跨核生产者/消费者融合 (Pairwise AIV-Producer/AIC-Consumer Fusion)"
description: "当流水线中存在独立的前置 VEC pass（如 dequant/cast），且硬件融合路径不可用时，将该 VEC pass 与 cube kernel 融合进单个 mix kernel：AIC ci 与其配对 AIV（2ci, 2ci+1）组成生产者/消费者对，AIV 按 AIC 的消费顺序生产中间数据到 write-once GM workspace，用 GM flag 协议同步，实现跨核软件流水，launch 数减 1 且 cast 与 cube 计算重叠。"
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

# Strategy X14: Mix-Kernel 跨核生产者/消费者融合 (Pairwise AIV-Producer/AIC-Consumer Fusion)

## 核心思路
当流水线中存在独立的前置 VEC pass（如 dequant/cast），且硬件融合路径不可用时，将该 VEC pass 与 cube kernel 融合进**单个 mix kernel**：AIC ci 与其配对 AIV（2ci, 2ci+1）组成生产者/消费者对，AIV 按 AIC 的消费顺序（如 (nIdx,kIdx) strip）生产中间数据到 write-once GM workspace，用 **GM flag 协议**同步（128B 步长 flag、MTE3 DataCopyPad 发布、AIC 侧 `__gm__ volatile` 有界轮询 + DCCI CACHELINE_ALL），实现跨核软件流水，launch 数减 1 且 cast 与 cube 计算重叠。

## 适用场景
- 三 kernel（或多 kernel）串行流水线，前置 VEC pass 占 kernel 时间比例显著（如量化 matmul 的独立 dequant pass）
- 硬件融合路径不可用（如 DAV_2201 ifMmadInstrSupportAntiQuant=false）
- c220 等平台上 CrossCoreSetFlag/WaitFlag（PIPE_S）非法、用户态 ffts 握手不成立时，GM-flag 是可靠替代
- 瓶颈类型：no_overlap / mte2_stall，且 profiling 显示独立 pass 与主计算串行

## 实现要点
- 配对关系因平台而异，需在目标平台确认（如 910B2C：AIC ids [0,24)、AIV ids [0,48)、GetBlockNum()=24）
- 生产顺序必须与消费顺序严格一致（strip 序）；write-once workspace 避免读写竞争
- 三大坑：(1) AIC 侧标量 GM 轮询读会被编译器 CSE 提升，必须 `__gm__ volatile` 指针读，否则空转；(2) AIV 标量 GM 写会丢失，必须用 MTE3 DataCopyPad 发布 flag；(3) 跨核 wait 是聚合阈值语义，SyncAll 为正确性必需（裸 set/wait 可致精度全挂）
- 生产者侧用 TQue 深度 2 流水化进一步隐藏 cast 延迟
- 保留 legacy 多 kernel 路径作环境变量回退，平台路由兜底

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
