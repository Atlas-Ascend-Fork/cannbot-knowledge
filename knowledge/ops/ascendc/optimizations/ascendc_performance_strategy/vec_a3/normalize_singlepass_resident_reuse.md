---
type: Optimization
title: 归一化类算子「统计遍 + 施加遍」两遍扫描改单遍驻留复用（整组一次向量链）
description: 将统计遍与施加遍改为单次搬入后片上驻留复用，避免施加阶段再次从GM搬入
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-normalize-singlepass-resident-reuse.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：归一化类算子「统计遍 + 施加遍」两遍扫描改单遍驻留复用（整组一次向量链）

> 单一优化点：group_norm / layer_norm / rms_norm 一类「先归约求统计量、再逐元素施加同一缩放因子」的归一化 kernel，若统计阶段把数据搬入片上后**丢弃**、施加阶段再从全局存储**重新搬入并按子段（逐通道/逐行）碎化处理**，则 GM 读了两遍、向量链碎成 O(子段数) 条。改为：数据一次搬入后全程驻留片上，统计（ReduceSum + x² 平面）与施加（单条整段向量链）复用同一驻留数据，最后一次写出。

**实测样本**：group_norm（无 affine），910B3，msprof kernel 硬件时间 P4 6.60→3.85us（**-42%**）、P10 5.20→4.08us、P1 2.68→2.18us；msprof pipe 前后对比可见 SCALAR 83%（队列生命周期/碎循环同步）主导显著下降。

---

## 1. 原理

归一化算子的数学结构：对每个分组 P（M 个元素）求 mean/var，再施加 `y = (x - mean) * rstd` ——**P 内所有元素共享同一对 (mean, rstd)**。因此施加阶段不存在任何按子段（通道/行）切分的必要性。反模式实现却常按子段切：

1. 统计 pass：整组搬入 UB，ReduceSum 后 buffer 即弃（有的实现还就地 `x = x*x` 破坏原始平面）。
2. 施加 pass：逐子段重新 DataCopyPad 搬入 → 每子段完整走一遍队列生命周期（AllocTensor/EnQue/DeQue/Free + DMA setup）→ 小向量链 → 逐子段写出。

代价：GM 读 2 遍（MTE2 流量 ×2）；子段数 × 队列生命周期与 DMA 发射（子段小时固定开销占比极高，msprof 表现为 SCALAR pipe >80%）；fp16 路径双重 widen Cast。

单遍重构：整组 DataCopyPad 入 UB（唯一 GM 读）→ widen 到 fp32 平面 **一次** → `ReduceSum(x)` + `sq = x*x; ReduceSum(sq)`（sq 落独立临时平面，**不破坏** xf）→ 单条整段向量链施加（fp32: Adds/Muls 直写输出；fp16: xf 原地 + 一次 CAST_RINT）→ 一次 DataCopyPad 写出。队列生命周期从 O(子段数) 到 1，MTE2 流量 ×2 → ×1。

## 2. 性能问题模式

命中本策略的典型反模式（任一）：

- kernel 里存在「统计函数 + 施加函数」两个阶段，施加函数内部重新从 GM 搬数据（CopyIn 出现两次）。
- 施加阶段按通道/行/子段循环，每子段独立 Alloc/EnQue/DeQue/Free + 小粒度 DataCopyPad + 短向量链。
- msprof：SCALAR pipe 占比 >60~80%（碎循环 + 队列同步），MTE2 搬入量 ≈ 2 × 输入字节。
- fp16 路径统计前 Cast 一次、施加前又 Cast 一次（双重 widen）。

不适用：分组数据量超过单核片上容量（须分块两遍或在线算法如 Welford）；施加因子子段间不相同的算子（如 instance_norm 之外的逐元素缩放）。

## 3. 正确性红线

- **平方平面不得就地覆盖原始平面**：`Mul(sq, xf, xf)` 的 dst 必须独立；若实现成 `Mul(xf, xf, xf)` 会破坏后续施加遍的数据（归一化结果全错，但小均值数据可能仍在容差内——必须看代码而非精度）。
- **host 侧片上容量公式同步更新**：新增临时平面（如 x² 4B/elem）后，`TORCH_CHECK(ubNeed <= limit)` 的 ubNeed 必须把新平面计入（fp32 路径 = 输入 2 buf + 输出 2 buf + fp32 平面 + x² 平面 + scratch）。
- **尾块语义**：widen（Cast/DataCopy）可按对齐量搬运（垃圾不参与统计），但 ReduceSum / Mul / 施加链必须按真实元素数 inner_，写出 DataCopyPad 按真实量截断。
- **负方差截断与 eps 位置保持原语义**（`var = max(0, E[x²]-mean²)`，`rstd = rsqrt(var+eps)`）。
- fp16 精度路径：统计与施加仍在 fp32 平面，仅输出前 CAST_RINT 回半精度（与原实现同舍入路径）。

## 4. 泛化条件

适用：
- 「归约求统计量 + 施加同组统一因子」的归一化家族：group_norm / layer_norm / rms_norm / batch_norm（单分组场景）。
- 分组数据可整组驻留片上（fp32 约 24B/elem 预算含双缓冲）。
- 施加阶段当前按子段碎化或重新搬入。

不适用：
- 分组超片上容量（改分块归约或在线统计）。
- 因子逐元素/逐子段不同（非统一缩放）。
- kernel-bound 已消除且 host 主导时，端到端收益会被掩盖（仍值得做——为 host 优化后留空间，kernel 硬件时间是客观指标）。

## 5. 实施步骤

1. 读现有 kernel，确认统计 pass 与施加 pass 的数据流（是否两遍搬入、施加是否碎化）。
2. 重构 ProcessGroup：一次搬入 → 一次 widen → ReduceSum(x) → 独立平面平方 + ReduceSum(sq) → 单向量链施加 → 一次写出。
3. host 侧容量公式 +（若需要）tiling 字段更新；按 32 对齐的 innerAligned 分配各平面。
4. 全量精度回归（重点 fp16 舍入路径与 zeros 输入 case）+ msprof 对比 kernel 硬件时间（不要只看端到端——host 主导时会掩盖 kernel 收益）。

## 6. LLM 前置问题（实施前自检）

- 施加的 (mean, rstd) 是否对整组统一？（不统一则本策略不适用）
- 分组最大元素量 ×（输入2buf + 输出2buf + fp32 + x²）是否 ≤ 片上容量？
- 平方运算的 dst 是否独立平面？host ubNeed 是否把新平面计入？
- ReduceSum/施加链的 count 是否用真实量而非对齐量？

## 7. 验收标准

- build + 精度全过；实测（无 affine，910B3，msprof kernel 硬件时间）：P4 6.60→3.85us（**-42%**）、P10 5.20→4.08us、P1 2.68→2.18us；msprof pipe 前后对比可见 SCALAR 83%（队列生命周期/碎循环同步）主导显著下降。重点回归 fp16 舍入路径与 zeros 输入 case，以 kernel 硬件时间为客观指标（host 主导时端到端会掩盖收益）。

## 检索卡（短卡）

动作：将统计遍与施加遍改为单次搬入后片上驻留复用，避免施加阶段再次从GM搬入
适用：同组共享统计因子的归一化，且分组数据可整组驻留片上
限制：平方计算必须使用独立dst，不能就地覆盖原始数据平面
范围：归一化kernel的单组统计与统一因子施加路径
检索词：group_norm、layer_norm、rms_norm、mean、var、rstd、片上驻留、CopyIn
机会：统计与施加分成两阶段，且施加函数重新从GM CopyIn同组数据
代价：受片上容量限制，要求整组数据能够驻留
