---
type: Optimization
title: "X24: AIC_ONLY 任务类型压设备 launch 地板（固定开销主导算子）"
description: "微小 shape、固定开销主导的算子（kernel 时间与 shape 几乎无关，cube_util 极低、标量占比高）其设备时间大部分是「每 AIC 调度启动」的固定开销，不是计算。"
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

# Strategy X24: AIC_ONLY 任务类型压设备 launch 地板（固定开销主导算子）

## 核心思路
微小 shape、固定开销主导的算子（kernel 时间与 shape 几乎无关，cube_util 极低、标量占比高）其设备时间大部分是「每 AIC 调度启动」的固定开销，不是计算。X24 把任务类型从默认 `KERNEL_TYPE_MIX_AIC_1_2`（1 AIC + 2 AIV）改为 **`KERNEL_TYPE_AIC_ONLY`**（纯 cube 核，不启动 AIV 向量核），去掉每 AIC 调度的 2 个空转 AIV 任务启动，压低设备固定地板。叠加紧凑 tiling 加载（GM 标量读取从全量 tiling 参数降为少量 int32）后逼近 910B 的 kernel launch 物理地板。

## 适用场景
- **算子类型**: 微小 shape matmul / elementwise / reduction 等固定开销主导算子；纯 cube 计算、无 AIV 侧必做工作
- **瓶颈类型**: `scalar_compute` / `no_overlap` / `compute_bound`（固定开销而非计算量主导）、cube_util ≪ 标量占比

## 实现要点
1. kernel 注册处声明 `KERNEL_TYPE_AIC_ONLY`（去掉 AIV 任务启动，降低每 launch 固定开销）
2. 配 compact tiling 头：manual 路径只读少量前置 int32（替代全量 tiling 参数逐标量加载）
3. 固定开销主导判定：不同 shape kernel 时间几乎相同 + cube_util 远低于标量占比
4. 与手动 mmad 分形加载（TQue CopyIn，非 LoadData3D）叠加

## 约束
- 纯 cube 算子收益最大；有 AIV 侧 epilogue/向量必做工作时不能盲目 AIC_ONLY
- 上限认知：910B 每 kernel launch 设备地板为数微秒级；目标加速比低于硬件地板时物理不可达，先确认目标可行性

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；全量精度门禁加逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带；固定开销主导需先用不同 shape 的同码 A/A 确认 kernel 时间不随计算量变化。
