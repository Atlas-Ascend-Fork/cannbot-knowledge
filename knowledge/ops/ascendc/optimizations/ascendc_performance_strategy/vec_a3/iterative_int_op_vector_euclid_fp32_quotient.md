---
type: Optimization
title: 迭代类整数逐元素算法改「fp32 商 + 整数精确修正」向量欧几里得型步进
description: 将逐元素标量或位迭代改为FP32求商、截断转换驱动的向量欧几里得迭代
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-iterative-int-op-vector-euclid-fp32-quotient.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：迭代类整数逐元素算法改「fp32 商 + 整数精确修正」向量欧几里得型步进

> 单一优化点：Vector 单元无整数除法/求余原语时，迭代类整数逐元素算法（GCD/LCM/模逆等）常退化为**逐元素标量循环**（GetValue/SetValue）或**位技巧型多轮全 tile 扫描**（Stein 二进制 GCD 的逐位迭代 + 每轮收敛轮询）。改用**向量欧几里得型步进**：用 fp32 `Div`（正确舍入）求商 + 整数域 `Mul/Sub` 修正余数（r<0 加 b、r≥b 减 b），一步等价多个位迭代；收敛轮询用**同 pipe 两段 WholeReduceMax + 单次标量读**（V_S 事件），替代跨 pipe `ReduceSum` + `PipeBarrier<PIPE_ALL>` 的全流水排空。

本策略适用于任何"迭代收敛类整数逐元素运算"的 kernel，与具体算子无关（以 Gcd 类算子为例）。

## 1. 原理

- **算法层**：Stein 二进制 GCD 每 tile 需固定 ~31 次提公因子迭代 + ≤96 次归一化迭代 + 31 次逐位左移还原，每次都是全 tile 向量遍历；欧几里得一步一个商（值域 < 2^24 时 5-10 个双步 pass 收敛）。向量单元吞吐下，pass 数 × 每 pass 指令数决定耗时——欧几里得的 Div 虽是重指令，但 pass 数少一个量级。
- **数值层（精确性构造）**：fp32 `Div` 正确舍入 ⇒ 商估计 q ∈ {n-1, n, n+1}；`r = a - q*b` 用整数 Mul/Sub（mod 2^32 回绕恒精确）落在 (-b, 2b)；两次整数修正（符号掩码 `r>>31` 或 fp32 单调比较）后 r ∈ [0, b) **精确**。|v| < 2^24 时 fp32 全精确；全范围 int32 用两级商精化（第二次 Div 修正残差）。
- **轮询层**：`ReduceSum<float, true>` 是跨 pipe 归约，后随 `PipeBarrier<PIPE_ALL>` 排空 MTE/V/S 全流水——每 2 次迭代一次即成瓶颈。两段 `WholeReduceMax`（64 lane → 32 partial → 1）全程留在 V pipe，只需一次 `SetFlag/WaitFlag<V_S>` 让标量核读结果，开销低一个量级。

## 2. 性能问题模式

1. 代码形态：kernel 内有**逐元素标量迭代循环**（`while (b != 0) { r = a % b; ... }` 配 GetValue/SetValue），或**固定位数上限的全 tile 向量位迭代**（每 lane 独立收敛后仍空转）。
2. 代码形态：每 k 次迭代做收敛检查，检查实现为跨 pipe 归约 + `PipeBarrier<PIPE_ALL>`。
3. profiling 特征：主 kernel 占 elapsed 96-100%，vec pipe 占比高；dtype 分派中窄整型（int16）在 host 侧 cast 链（Cast/BroadcastTo/TensorMove 额外 kernel），宽整型（int64）落到标量回退。
4. 逐 case 特征：宽整型 case 慢 5-10x（标量回退），窄整型 case 慢 3-5x（迭代数 × 轮询开销）。

不适用：非迭代收敛型整数运算（单步可表达）；数据强依赖跨 lane 通信；int128 级值域（两级精化也不够，需另构造）。

## 3. 正确性红线

- **fp32 值域门控**：int32/int64 输入 |v| ≥ 2^24 时 fp32 不精确——必须要么走两级商精化路径（int32 全范围），要么 tile 级 `ReduceMaxF32` 门控回退标量（int64）。门控用的 max 必须在 fp32 域单调正确。
- **A2/A3 逻辑指令 count 陷阱**：And/Or/Not 在 int32 上调用可编译但 count 按 int16 元素解释，破坏后半数据——全程避开逻辑运算，用 `Compare/Select`、移位符号掩码（`r>>31` ∈ {0,-1}）、`Max/Min` 算术掩码替代。
- **INT_MIN 绝对值**：`|INT_MIN|` 回绕为自身——用 Euclid 恒等变换（gcd(2^31, b) == gcd(2^31 - b, b)）做 lane 替换，b==0 lane 保留原位模式。
- **FFTS HW-loop 陷阱（bisheng/910B3）**：可数纯向量循环体被降低为坏掉的硬件循环（aicore 507015 "loopend before loop"）——迭代循环保持**数据依赖退出**（收敛即 break），或直线代码；收敛轮询的存在恰好提供了数据依赖。
- **frozen lane 两步恒等**：收敛 lane (a, 0) 在双步设计中必须映射回自身（div-by-zero 的 inf/NaN 被 Select 掩码 *0 湮灭），否则多执行的 pass 破坏已收敛值。
- **Select 的 payload 传输**：int32 数据借 `ReinterpretCast<float>` 视图过 Select（VSEL_TENSOR_TENSOR_MODE）保 bit 精确。

## 4. 泛化条件

适用（任一）：
- 迭代收敛类整数逐元素算法（gcd/lcm/扩展欧几里得/离散对数步进等），Vector 无对应原语。
- 现实现为逐元素标量循环或位技巧型多轮全 tile 扫描 + 跨 pipe 收敛轮询。
- 窄整型在 host 侧 cast 链放大框架开销、宽整型无向量路径。

不适用（任一）：
- 单步可表达的整数运算（直接用向量指令）。
- 值域超出两级精化能力（如 int64 全域相除）且无法 tile 级门控回退。
- 搬运/带宽主导（计算重构收益被掩盖）。

## 5. 实施步骤

1. profiling 确认主 kernel 96%+ 占比、vec 主导；定位标量回退 dtype 簇与迭代结构。
2. 构造精确整数取余原语：fp32 `Div` → trunc Cast → int `Mul`/`Sub` → 修正（先试单修正：小值域 < 2^18 可用向下偏置乘子 `Muls(1-2^-20)` 消掉 r<0 分支）。
3. 实现双步/pass 主循环（frozen lane 两步恒等），收敛轮询用两段 `WholeReduceMax` + `V_S` 事件 + 单次 `GetValue`。
4. dtype 分派收进 kernel：int16 直接 fp32 精确域；int64 用 `ReduceMaxF32` 门控 + 超界标量回退；host 侧去掉 cast/broadcast_tensors 物化。
5. UB 预算：tile = 单 chunk（如 2048 elem），工作区 = 每 int32/fp32 缓冲一份 + mask/归约小缓冲。
6. 全量编译 + 精度（int exact match）+ 性能多次取样；对照噪声阈值判定。

## 6. LLM 前置问题

- 算法是否迭代收敛、每 lane 独立？现实现 pass 数上限多少（bits 上限 vs 实际收敛分布）？
- 值域是否 < 2^24（fp32 精确域）？超界时用两级精化还是 tile 级门控回退标量？
- 收敛轮询现在用什么归约/屏障？能否改成同 pipe 两段 WholeReduceMax + V_S？
- 是否踩了 And/Or int32 count 陷阱、INT_MIN 绝对值、FFTS HW-loop 陷阱？
- 窄整型是否还在 host 侧 cast？能否 kernel 内直算 + RINT 回写？

## 7. 验收标准

- build + 精度全过（int exact match：输出值与 indices/符号位模式 bit 级一致；fp32 值域门控正确——int32 全范围走两级商精化、int64 超界 lane 走 tile 级门控标量回退，frozen lane 两步恒等不被多执行 pass 破坏）。
- 性能验收：宽整型（原标量回退，慢 5-10x）与窄整型（原位迭代+轮询，慢 3-5x）case 加速比提升均超噪声阈值；主 kernel 仍占 elapsed 96%+（未引入额外 host cast 链 kernel）。
- 非适用场景（单步可表达运算、搬运/带宽主导）不套用本策略，保持原路径且无精度/性能退化。

## 检索卡（短卡）

动作：将逐元素标量或位迭代改为FP32求商、截断转换驱动的向量欧几里得迭代
适用：整数逐元素迭代收敛算法，且Vector没有对应整数原语
限制：仅在FP32可精确表达的值域内使用；|v|≥2^24时不精确
范围：GCD、LCM、扩展欧几里得等整数逐元素算法
检索词：Stein二进制GCD、欧几里得、FP32 Div、trunc Cast、整数取余
机会：kernel存在GetValue/SetValue标量取余循环，或固定位数的全tile向量迭代
