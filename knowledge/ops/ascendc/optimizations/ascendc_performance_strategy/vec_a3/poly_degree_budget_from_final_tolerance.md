---
type: Optimization
title: 超越函数多项式次数按最终容差预算最小化（economization + 配套魔数取整）
description: 依据最终容差和误差传递预算，最小化软件超越函数的多项式展开次数。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-poly-degree-budget-from-final-tolerance.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：超越函数多项式次数按最终容差预算最小化（economization + 配套魔数取整）

> 单一优化点：elementwise 数学算子（激活类）kernel 里为满足精度而使用的软件超越函数（exp/ln/tanh 的 Taylor 展开），其展开次数往往按"中间量精度"而非"**最终输出容差**"选择，普遍 overkill。应从最终容差（atol/rtol）出发，沿误差传递链（衰减因子、饱和压缩）算出中间超越函数的**相对误差预算**，再用区间 economized minimax 多项式（Chebyshev 经济化）把次数降到预算允许的最低——每降 1 次省 2 条向量指令。

## 1. 原理

- 容差预算倒推：最终判据 `|y-g| <= atol + rtol*|g|`。沿计算链做误差传递分析，找出中间量的等效相对误差上限 ε；例：`t = v/(v+2)` 型有理式对分子的相对误差传递因子 `2/(v+2) <= 1`（饱和区压缩），于是 exp 的 ε 可以取到接近最终 rtol 的量级，而非"越高精度越好"。
- 次数选择：区间 [−a, a] 上 Taylor 截断误差 ~ `a^(n+1)/(n+1)!`，而 **economized minimax**（Chebyshev 最小二乘/经济化）同次数再低约一个数量级：实例中 [-0.5,0.5] 上 Taylor deg7（1.6e-7，14 条指令）被 deg5 minimax（1.16e-6，10 条指令）替代，全链 worst diff/tol 仅 0.028（36x 余量）。
- 配套取整：范围缩减需要 rint(x)；高阶 `Round` API 内部展开多条指令，`|x| < 2^22` 时用魔数法 `(x + 1.5*2^23) - 1.5*2^23`（两条基础指令，RNE 语义）等价替代。

## 2. 性能问题模式

- msprof 显示 aiv vec 占比 >90%（纯 VEC 计算瓶颈），Compute 段是软件超越函数长链。
- 代码形态：`lib/math/exp.h` 的 `Exp<float, 10>`（level 10 Taylor）或手写 8-9 项级数，"精度优先"直接拉满次数。
- 加速比随数据量增大而恶化、与 dtype 容差无关（fp16/bf16 宽容差 case 也在跑高精度路径）。

不适用：
- 容差本身达 0 ulp / 逐比特一致要求（如需与参考实现 bit 级对齐）。
- 误差传递链上存在 catastrophic cancellation 的表达式（`1-小量` 形态）——先重构表达式再谈降次。
- 搬运/带宽主导（vec 占比低）——降次无感。

## 3. 正确性红线

- **预算必须留给链上其他误差源**：中间舍入（每条 Horner 步 ~0.5 ulp）、范围缩减的 r 计算、整数指数路径的指令精度，合计后再对最终容差留 ≥2x 余量；用 fp32 逐指令模拟（numpy 按真实顺序 cast）在**全部评测 value_range（含 ±边界、±inf、NaN）**上扫 worst diff/tol，>0.5 即降一档。
- **Chebyshev 窗口换算**：`Chebyshev.fit(domain=[-a,a])` 的系数在 u=x/a 窗口上，`cheb2poly` 后须乘 `a^-k`... 谨慎：是乘 `a^k` 缩放回 x 幂基（实例：u=2r 时乘 2^k），忘记换算会引入 % 级错误。
- **区间闭边界**：rint 用 RNE 或 half-away 决定 r 落在 [-a,a] 还是 (-a,a]，多项式误差按闭区间评估。
- **特殊值端点**：±inf/NaN 的路径要单独核对（下溢 clamp 下限须让 e^x 精确为 +0.0，才能让 `-inf * 0 = NaN` 与 golden 的 equal_nan 对齐）。

## 4. 泛化条件

适用：任何含软件 exp/ln/tanh/sin 的 elementwise kernel，最终容差 ≥1e-5 相对量级。
不适用：见 §2。

## 5. 实施步骤

1. 写 fp32 逐指令模拟（numpy，按 kernel 相同顺序与 cast 点），先验证**当前**实现的 worst diff/tol 作基线。
2. 推导误差传递：写出最终公式对各中间量的敏感度，取最宽的 ε 预算。
3. `Chebyshev.fit` on 缩减区间 → cheb2poly → 窗口换算 → 幂基系数；模拟验证降次后全值域 worst diff/tol ≤0.5。
4. kernel 内替换：Horner 起步用 `Duplicate(c_{n-1}) + Axpy(r, c_n)`（省 1 条），其余每步 Mul+Adds。
5. rint 换魔数法（确认 |x| 上界 < 2^22）。
6. 全量精度 + 性能回归；msprof 复核 vec 时间按 op 数比例下降。

## 6. LLM 前置问题

- 最终容差多少？误差传递链上最坏的放大/衰减因子是多少？
- 当前实现的多项式误差 vs 预算差几个数量级（overkill 倍数）？
- 评测值域有没有 ±inf/NaN/±极大值端点？clamp 边界是否让特殊值语义（-inf→NaN）与 golden 对齐？

## 7. 验收标准

- build + 精度全过；fp32 逐指令模拟在全部评测 value_range（含 ±边界、±inf、NaN）上 worst diff/tol ≤0.5（实例：Taylor deg7（1.6e-7，14 条指令）被 deg5 minimax（1.16e-6，10 条指令）替代，全链 worst diff/tol 仅 0.028，36x 余量）；msprof 复核 vec 时间按向量指令数减少比例下降。

## 检索卡（短卡）

动作：依据最终容差和误差传递预算，最小化软件超越函数的多项式展开次数。
适用：含软件exp、ln、tanh或sin的elementwise核，最终相对容差不低于1e-5量级。
限制：误差预算必须为计算链上的其他误差源保留余量。
范围：激活类elementwise数学kernel。
检索词：exp、ln、tanh、sin、Taylor展开、Horner、误差传递、最终容差。
机会：aiv vec占比超过90%，Compute段存在软件超越函数长链。
