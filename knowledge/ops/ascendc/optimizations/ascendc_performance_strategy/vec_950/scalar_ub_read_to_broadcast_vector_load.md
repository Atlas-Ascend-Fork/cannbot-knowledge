---
type: Optimization
title: 逐 lane 标量 UB 读 → 单条广播向量装载
description: 把 VF 热循环里的标量 UB 读加 Muls 换成一条 DIST_BRC_B32 广播装载加寄存器 Mul
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/scalar-ub-read-to-broadcast-vector-load.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：逐 lane 标量 UB 读 → 单条广播向量装载

把 VF 热循环里的 `const float c = ptr[i];` 标量 UB 读 + `Muls` 改成 1 条 `Reg::LoadAlign<..., LoadDist::DIST_BRC_B32>` 广播装载 + `Reg::Mul`；语义等价（同一标量、同一舍入），只换取数路径。

## 1. 原理

VF 里的标量 UB 读走的是**辅助标量单元**，它有两条隐性成本：

1. 标量读与向量乘分属两个单元，编译器要插入一次跨单元同步，于是“读系数 → 乘”变成两步串行；
2. 该标量恰好在乘法操作数的关键路径上，`n` 轴有 N 个系数就串行 N 次。

`DIST_BRC_B32` 广播装载把这件事变成**一条向量指令**：它从一个 32-bit 地址把标量广播到全部 lane，结果直接落在向量寄存器里，于是 `Mul(dst, src, brc)` 是一条普通向量乘，不再经过标量单元、也没有跨单元同步。语义完全等价（同一标量、同一舍入），只是取数路径换了。

收益随 `n` 轴长度线性：每个 (step, n) 少一次标量读，n 越大省得越多。

实现机制：把 `const float c = row[i]; ... Muls(acc, x, c, mask);` 改成 `LoadAlign<float, LoadDist::DIST_BRC_B32>(cReg, row + i); ... Mul(acc, x, cReg, mask);`，必要时把 `Muls` 换成三操作数 `Mul`（`Muls` 的第二操作数是标量，`Mul` 的是寄存器）。

## 2. 性能问题模式

- 优化目标：消除 VF 热循环里的标量 UB 读及其跨单元同步，把“读系数 + 乘”折叠成一条向量乘。
- 适用数据流：任何在 VF 内用“逐元素系数表”做缩放的 kernel：scan / prefix / RNN 的逐位置系数、归一化的逐行 scale/bias、注意力的逐位置掩码系数等。

## 3. 正确性红线

- 被广播的必须是**单个标量**（同一行内所有 lane 共用同一值）；逐 lane 不同的系数不能用
- 系数地址须按元素宽度对齐（fp32 4B / fp16 2B），否则广播装载可能非法
- `Muls`（第二操作数标量）必须改成 `Mul`（第二操作数寄存器），否则编译器仍会走标量单元
- 同一 kernel 里若有多个取数路径（如多 phase / 多分支副本），必须**全部**改，否则收益只落在一半

## 4. 泛化条件

- 策略作用域：任何在 VF 内用“逐元素系数表”做缩放的 kernel：scan / prefix / RNN 的逐位置系数、归一化的逐行 scale/bias、注意力的逐位置掩码系数等。

适用：

- VF 热循环里存在逐 (step, n) 的标量 UB 读，且该标量参与一次向量乘/加
- `n` 轴或 `step` 轴足够长（≥8）使串行次数显著
- 后端提供 `DIST_BRC_B32` 广播装载原语

不适用：

- 系数逐 lane 不同（需 gather / 向量表，不是广播）
- 标量读已不在关键路径上（被完全重叠）
- 后端不提供广播装载原语
- 与 `brc-weight-register-acc-batch-fma` 的分工：那张卡是“把逐行 VF 调用批处理”的大重构，广播装载只是它四个配料之一；本卡是**单点替换**——循环结构不动，只把热循环里的标量 UB 读换成一条广播装载，适用于不适合批处理的形态。

## 5. 实施步骤

1. 在 VF 里搜索形如 `const float c = ptr[...];` 后接 `Muls/Adds` 的模式
2. 把标量读改成 `LoadAlign<float, LoadDist::DIST_BRC_B32>(cReg, ptr + i)`
3. 把 `Muls/Adds` 改成 `Mul/Add`（第二操作数换成寄存器）
4. 检查同一 kernel 的所有副本（不同 phase / 不同 LAYOUT 分支）都改到
5. 用逐例 MERE/MARE 确认等价（广播装载与标量读取的是同一个值，应当逐位一致）

## 6. LLM 前置问题

- 被广播的是单个标量吗（同一行所有 lane 共用）？
- 系数地址按元素宽度对齐了吗？
- `Muls/Adds` 是否已改成 `Mul/Add`（寄存器操作数）？
- 同一 kernel 的所有副本都改到了吗？

## 7. 分类与关联

- Classification：`validated_strategy`
- Generality：`common`
- 相关策略：`brc-weight-register-acc-batch-fma`（广播装载的批处理形态）

## 检索卡（短卡）

动作：把 VF 热循环里的标量 UB 读加 Muls 换成一条 DIST_BRC_B32 广播装载加寄存器 Mul
适用：VF 热循环存在逐 (step,n) 标量 UB 读且参与一次向量乘/加；n 或 step 轴≥8
限制：被广播的必须是行内共用的单个标量；系数地址须按元素宽度对齐；Muls 必须换成三操作数 Mul
范围：递推/扫描/归一化等用逐元素系数表缩放的 VF 内核
检索词：DIST_BRC_B32、广播装载、Muls→Mul、标量 UB 读、跨单元同步、LoadAlign
机会：热循环每步一次标量 UB 读，带出跨单元同步与标量发射
代价：同一内核若有多套副本路径须全部改，否则收益只落一半
