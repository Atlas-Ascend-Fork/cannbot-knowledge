---
type: Optimization
title: 递推链超越函数降阶重拟合（相对误差 minimax）
description: 把超越函数的多项式从 Taylor 重拟合为相对误差 minimax，阶数当优化变量，并删掉区间守卫与兜底 Select
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/transcendental-minimax-refit.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：递推链超越函数降阶重拟合（相对误差 minimax）

把跨步递推里的 `dA = exp(delta*A)` 从「高阶 Taylor + 区间守卫 + vexp 兜底 + Select」改为「低阶相对误差 minimax」（fp32）与「单条 intrinsic」（16-bit）：用更低的阶数拿到更小的有符号偏差，并删掉守卫。

## 1. 原理

长递推里的超越函数误差会被 L 步**相干累积**，所以判据必须是有符号平均偏差（signed mean bias），不是单次最大相对误差。这带来一个反直觉结论：**更高阶不等于更准**。

Taylor 展开优化的是 absolute error（它的天然度量），而递推放大的正是系统偏置；相对误差 minimax 拟合（`min max |P−f| / f`）可以在低阶就把有符号偏差压到接近 0。在幅值小、符号单一的递推增量域上，低阶 minimax 的有符号偏差可以比高阶 Taylor 更小，指令数也更少。

第二个成本点是**区间守卫本身**：`|x| ≤ thresh` 的守卫需要 Abs + Compares + 兜底 intrinsic + Select，把多项式本身的收益全部吃掉。若契约 value_range 已保证落在拟合域内，守卫是纯浪费；有域外风险时应**扩大拟合域或在 host 侧拒绝**，而不是每条 lane 都做 Select。

实现机制：① 用相对误差 minimax（对采样点做线性规划）替代截断 Taylor，阶数取“有符号偏差 < 0.01 ulp”的最低阶；② 系数用 `Duplicate` + `MulDstAdd`(FMA) 的 Horner 链，每 slice 一次广播；③ 删掉 Abs/Compares/兜底 intrinsic/Select 守卫，域由 host 契约保证；④ 16-bit dtype 用 `if constexpr` 分支直接走 1 条 `Reg::Exp`；⑤ 同时删掉守卫占用的寄存器与 mask；⑥ 用长递推的端到端精度（含相消区）验证，而不是只看单点误差。

## 2. 性能问题模式

- 优化目标：在压住（甚至降低）系统偏置的前提下，把每步超越函数的指令数显著降下来。
- 适用数据流：跨步递推（scan / prefix / RNN 类）里的 exp / log / tanh 计算链；fp32 走重拟合、16-bit 走 intrinsic。

## 3. 正确性红线

- **位级（bit-exact）护栏下不适用**；必须是容差型护栏（含“相消/小值域”这类统计型兜底判据）
- 拟合域必须覆盖契约 value_range；覆盖不到的部分在 host 侧拒绝或扩大拟合域，不得靠每条 lane 的 Select 兜底
- 系数必须以 fp32 常量硬编码，并注明求解方法与 ulp 偏差
- fp32 的误差论证不可直接搬给低精度 dtype，需单独做容差核算
- Horner 的累加器与乘数必须是**不同寄存器**（dst 既当累加器又当输出）

## 4. 泛化条件

- 策略作用域：op_class：跨步递推（scan / prefix / RNN 类）里的 exp / log / tanh 计算链；fp32 走重拟合、16-bit 走 intrinsic。

适用：

- 超越函数在 aiv_vec 侧占显著份额（≥20% 的向量指令），或每步被调用 N 次（N 为 n 轴长度）
- 护栏为容差型，且契约 value_range 可解析地界定拟合域
- 存在“更高阶 + 区间守卫”的当前实现，且其有符号偏差并未明显优于低阶 minimax

不适用：

- bit-exact 护栏（必须逐位一致）
- 契约域无法界定 / 输入分布无上界
- 超越函数只占 <10% 向量指令（收益被其它 pipe 隐藏）

与相邻策略的分工：

- 与 `transcendental-chain-algebraization` 的分工：那张卡的动作是“级数截断 / 精确代数恒等式”，没有把**阶数与误差度量**当优化变量；本卡把“阶数 + 相对误差 minimax + 守卫删除”当主变量，判据从“max 相对误差”改成“有符号平均偏差”。同一族问题可以叠加：先做代数化，再用本卡降阶。

## 5. 实施步骤

1. 在 CPU 上用 fp64 扫描契约域，同时看 **最大相对误差** 与 **有符号平均偏差** 两个指标
2. 对 `|P−f|/f` 做 minimax 线性规划，从 deg-3 起逐阶试，取“偏差 < 0.01 ulp”的最低阶
3. 把系数写成 `constexpr float`，kernel 里用 `Duplicate` 一次广播 + Horner `MulDstAdd` 链
4. 删掉 `Abs / Compares / 兜底 intrinsic / Select` 守卫；域外风险改由 host 侧 TORCH_CHECK 拒绝
5. 16-bit dtype 用 `if constexpr` 分支直接走 intrinsic
6. 删掉守卫占用的寄存器与 mask
7. 用长递推的端到端精度（含相消区）验证，而不是只看单点误差

## 6. LLM 前置问题

- 护栏是容差型还是 bit-exact？bit-exact 下本策略不适用。
- 契约 value_range 能否解析地界定拟合域？域外靠什么拒绝？
- 当前实现的有符号平均偏差是多少 ulp？如果已经 <0.01 ulp 就没有收益。
- 超越函数占向量指令的多少比例？低于 10% 时收益会被其它 pipe 隐藏。
- Horner 的累加器与乘数是不同寄存器吗？

## 7. 分类与关联

- Classification：`validated_strategy`
- Generality：`op_class`
- 相关策略：`transcendental-chain-algebraization`（代数化简的另一路径）、`distribution-gated-cheaper-prf-substitution`

## 检索卡（短卡）

动作：把超越函数的多项式从 Taylor 重拟合为相对误差 minimax，阶数当优化变量，并删掉区间守卫与兜底 Select
适用：超越函数占向量指令≥20%，或每步被调 N 次；护栏容差型且域可界定
限制：bit-exact 护栏不适用；拟合域须覆盖契约 value_range，域外靠 host 拒绝；Horner 累加器与乘数须不同寄存器
范围：跨步递推/扫描类算子的超越函数计算链
检索词：相对误差 minimax、阶数降阶、有符号平均偏差、守卫删除、MulDstAdd、intrinsic
机会：高阶 Taylor 加区间守卫加 vexp 兜底指令数远超低阶 minimax，而有符号偏差反而更大
代价：删守卫后域外输入静默出错，只能靠 host 契约拒绝
