---
type: Optimization
title: pooling backward 按窗口几何分派与向量 Gather 展开
description: 将标量gather/scatter循环改为host几何分派：等尺寸走平面纯拷贝，三轴整数倍走向量Gather。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-pooling-backward-geometry-dispatch-gather.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：pooling backward 按窗口几何分派与向量 Gather 展开

> 单一优化点：pooling 族 backward 的标量 gather/scatter 三重循环（SCALAR pipe 占比 >90%）改为 host 按窗口几何形态分派（等尺寸纯拷贝 / 整数倍向量 Gather 展开 / 通用路径），并以平面级并行切分提升小 batchChannels shape 的核利用率。

## 1. 原理

1. **host 按窗口几何分派**（形态判定零成本）：
   - 等尺寸（kd=kh=kw=1）→ 逐输出平面 MTE2→MTE3 纯拷贝
   - 整数倍下采样（dIn%dOut==0 等三轴同时成立）→ 向量 Gather 展开路径
   - 一般形态 → 通用路径（标量或后续向量化）
2. **整数倍路径核心性质**：每输入位置恰被 1 个输出位置覆盖，
   gi[id,ih,iw] = go[id/kd, ih/kh, iw/kw]·invDen —— 分段常数映射。
   每输出平面数据流：MTE2 读源平面 → Cast fp32 → Muls(invDen 标量) →
   **AscendC::Gather 整平面展开**（dst[i]=src[idx[i]]，idx 为字节偏移表）→ Cast 回 native → MTE3。
3. **平面级并行切分**：totalPlanes=batchChannels×dIn 均分到核，替代整 image 切分
   ——小 batchChannels shape（如 BC=3）核利用率从 7.5% 升到满载。
4. **索引表每核一次增量生成**（免逐元素除法），存 UB uint32 表。

## 2. 性能问题模式

pooling 族 backward（adaptive_avg_pool2d/3d 等"窗口均摊梯度"算子），输入输出空间比存在
等尺寸/整数倍/一般三种窗口几何形态之一，且原始实现为标量 gather/scatter 三重循环
（SCALAR pipe 占比 >90%）。

## 3. 正确性红线

- Gather 的 dst/src/srcOffset 起点必须 32B 对齐；表 stride 按 8 元素（uint32）对齐
- **标量 SetValue 生成的表被 V pipe 读（Gather/Mul）前必须 SetFlag/WaitFlag<S_V> 同步**
  （S 与 V 并发写读同一 UB 区是数据竞争；INTMUL 偶然通过只是 MTE2 长搬运掩盖时序）
- MTE3 方向 DataCopyPad 只接受 3 参数（无 padParams）；MTE2_MTE3 事件用于纯搬运同步
- 精度对齐 golden：预乘在 fp32 域（x·invDen 与 x/den 差 ≤2ulp fp32 ≪ 常规容差）；
  bf16 输出用 CAST_RINT，fp16 用 CAST_NONE；nan/inf 经 Muls/Gather 原样传播

## 4. 泛化条件

- **适用**：pooling 族 backward（adaptive_avg_pool2d/3d 等"窗口均摊梯度"算子），窗口几何为等尺寸/整数倍/一般三种形态之一；小 batchChannels shape 的平面级切分收益显著。
- **不适用**：仅 A2/A3 验证（Gather API A2 可用；MTE2_MTE3 事件存在性按 CANN 版本确认）；单平面数据需 fit UB（hwIn/hwOut ≤ 8192 fp32 元素量级）。

## 5. 实施步骤

1. host 判定形态（sameSize/intMul/vecOk），扩展 tiling 或标量传参 mode/kd/kh/kw
2. kernel 增加 fastpath 分支与平面切分（planeFirst/planeCount）
3. 索引表生成（增量扫描）+ S_V 同步
4. 每平面 5 步数据流（读/Cast/Muls/Gather/Cast/写），平面间 PipeBarrier

## 6. LLM 前置问题

- 算子是否属于 pooling 族 backward（窗口均摊梯度），SCALAR pipe 占比是否 >90%？
- 输入输出空间比是否落在等尺寸/整数倍/一般三种窗口几何形态之一？
- 单平面数据（hwIn/hwOut）是否能 fit UB（≤ 8192 fp32 元素量级）？
- 目标芯片是否为 A2/A3（Gather API 与 MTE2_MTE3 事件是否可用）？

## 7. 验收标准

- build + 精度全过；adaptive_avg_pool3d_backward（910B3）：P20 8205→101us（81×）、P17 29.5×、P3 27.8×、P2 13.9×；geo vs 原实现 3.11×，均值 9.57×；精度 20/20（含 nan/inf/±65504/±3e38）。

## 检索卡（短卡）

动作：将标量gather/scatter循环改为host几何分派：等尺寸走平面纯拷贝，三轴整数倍走向量Gather。
适用：pooling族backward，窗口几何属于等尺寸、三轴整数倍或一般形态。
限制：Gather各起点须32B对齐，表stride须按8个uint32元素对齐。
范围：adaptive_avg_pool2d/3d等窗口均摊梯度backward路径。
检索词：窗口几何分派、sameSize、intMul、向量Gather、MTE2→MTE3、平面切分。
机会：存在标量gather/scatter三重循环，且SCALAR pipe占比超过90%。
代价：小batchChannels需检查平面级切分的核利用率。
