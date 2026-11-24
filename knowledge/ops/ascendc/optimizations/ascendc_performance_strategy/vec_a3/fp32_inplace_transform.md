---
type: Optimization
title: fp32 原地 Transform（删除恒等中转拷贝）
description: fp32 分支从先做 Adds 恒等中转改为直接在输入队列 tensor 上执行 Transform/计算。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-fp32-inplace-transform.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：fp32 原地 Transform（删除恒等中转拷贝）

> 单一优化点：计算 dtype 与输入 dtype 相同的 kernel 不再先做恒等搬运（`Adds(dst, src, 0.0f)`）再计算，直接在输入队列 tensor 上做 Transform/计算。

> ⚠️ **库内状态：需人工复核（高风险）**。8 轮实测 **0 轮有效**（5 轮 keep 均 <1.035×、3 轮精度失败 0/20 或 3/26）。原卡把恒等中转当纯死代码，**未识别它在 TQue 双队列架构下兼任 VECIN→VECOUT 的同步载体**。采纳前必须逐条核对 §3 红线与收益预检，否则会拆掉隐式同步链导致精度事故。

## 1. 原理

- 计算 dtype 与输入 dtype 相同的 kernel 仍先做恒等搬运（`Adds(dst, src, 0.0f)`）再计算——每 tile 白付一条全长向量指令（本案例占向量指令 1/3）。
- fp32 分支直接在输入队列 tensor 上做 Transform/计算，删除中转拷贝；半精度仍走 Cast 升精度。
- 改动量级：基础策略（一行分支，零风险）。

## 2. 性能问题模式

- 计算 dtype 与输入 dtype 相同的 kernel 仍先做恒等搬运（`Adds(dst, src, 0.0f)`）再计算——每 tile 白付一条全长向量指令（本案例占向量指令 1/3）。

## 3. 正确性红线

- 仅 fp32（计算 dtype 与输入 dtype 相同）分支可删中转拷贝；半精度仍必须走 Cast 升精度。
- **同步载体红线（关键，原卡缺失）**：若被删的恒等中转是 VECIN→VECOUT 队列间**唯一**的 V 级数据搬运（纯拷贝/位透传类算子，如 `view_as_complex_copy`、`indices_copy`、`foobar`），删除它会同时删除隐式同步链——CopyOut 直接消费 VECIN tensor 时 MTE2 与 MTE3 是独立引擎，缺 MTE2→MTE3 显式定序会读到未装载/被覆盖数据。本 bisheng 直编栈上已验证 4 种补法（手工 HardEvent / 换队列持有 / S 管栅栏 / 去预置）**全部失败**，此类算子**直接判不适用**。
- **发射级重叠红线**：恒等中转删后若 CopyOut 直写同一 slot，会失去原双 buffer 的发射级 load/store 重叠；仅当被删指令是纯开销（无重叠可失去）时才适用（`indices_copy` 即因同 slot 直写反而串行化）。

## 4. 泛化条件

- **适用**：计算 dtype 与输入 dtype 相同（如 fp32）的 kernel，存在恒等搬运中转的形态，且该中转**不是** VECIN→VECOUT 唯一的 V 级搬运。
- **不适用**：
  - 半精度输入需升精度计算的场景（仍需 Cast 中转）。
  - 纯位透传/拷贝类算子（中转是唯一 V 级搬运，删除即拆同步链）。
  - 混 dtype 算子中 fp32 case 占比过低（收益被半精度 case 稀释，见下方收益预检）。
- **收益预检（新增）**：预期加速 ≈ `fp32_case 占比 × 恒等指令占 vec 链比例`，两者乘积 <5% 不选。反例：cholesky 的 8 个 fp32 case 组内 +19.9%，但 12 个半精度 case 回退，8/20 权重稀释后仅 +3.1%；该卡真实受益面是「fp32 + 小 n」的双重子集。

## 5. 实施步骤

1. fp32 分支直接在输入队列 tensor 上做 Transform/计算。
2. 删除中转拷贝（`Adds(dst, src, 0.0f)` 形态）。
3. 半精度分支保持 Cast 升精度路径不变。

## 6. LLM 前置问题

- kernel 中是否存在计算 dtype 与输入 dtype 相同时的恒等搬运？
- 该恒等搬运占向量指令比例是否显著（如 1/3）？
- 半精度分支是否保留了 Cast 升精度路径？

## 7. 验收标准

- build + 精度全过；geo 0.6066→0.6333；P20 222→162us（0.45→0.61x）、P18 128→70us（0.20→0.37x）。
- **（新增）混 dtype 算子必须输出分 dtype 子集 geomean**：fp32 子集与 half/bf16 子集分别报告，避免聚合值掩盖半精度回退（cholesky 聚合 1.0314 掩盖了 bf16 子集 -11.1%）。
- **（新增）签名/封装改动红线**：为 fp32 直返 staging tensor 而修改 helper 签名（引用传出→按值返回）会对全部模板实例生效，可能给未触碰的 half 分支带来每调用固定开销；half 分支应保留旧签名/旧封装。

## 检索卡（短卡）

动作：fp32 分支从先做 Adds 恒等中转改为直接在输入队列 tensor 上执行 Transform/计算。
适用：适用于计算 dtype 与输入 dtype 相同且存在恒等中转搬运的 kernel。
限制：仅同 dtype 的 fp32 分支可删除中转；半精度仍必须 Cast 升精度；高风险：恒等中转若为 VECIN→VECOUT 唯一 V 级搬运则删除即拆同步链（不适用）；混 dtype 算子须按 fp32 case 占比预检收益
范围：计算与输入 dtype 相同的 fp32 kernel 分支。
检索词：fp32、Adds 恒等搬运、Transform、输入队列 tensor、Cast
机会：同 dtype kernel 每个 tile 仍执行一次 Adds 恒等搬运。
