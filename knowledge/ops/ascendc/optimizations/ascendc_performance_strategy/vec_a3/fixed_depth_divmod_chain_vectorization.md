---
type: Optimization
title: 固定深度整数 divmod 链的向量化解法（偏置倒数 + 单侧符号修正 + f32 桥接扩宽）
description: 采用偏置倒数qF=fl(rem×fl((1+2^-22)/base))，向量化固定深度标量整数除模链。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-fixed-depth-divmod-chain-vectorization.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：固定深度整数 divmod 链的向量化解法（偏置倒数 + 单侧符号修正 + f32 桥接扩宽）

> 单一优化点：Vector 单元无整数除法原语（A2 的向量 `Div` 仅 half/float）时，**固定深度的逐元素整数除模链**（混合进制 unravel、坐标解码、分桶下标等，每元素恰好 K 次 `%`/`//`，K=ndim 类常量）常退化为逐元素标量循环（标量除法 20-30 cycle/次 + GM 标量读 + SetValue 标量写，scalar_ratio 高达 98%+）。改用**逐轴向量链**：`Cast(i32→f32) → Muls(偏置倒数) → Cast(f32→i32, TRUNC) → Muls(base) → Sub → ShiftRight(31) 符号掩码单侧修正`，每轴 ~9 条向量指令处理整 tile；结果扩宽 int64 用 **f32 桥接**（`i32 → f32 → i64(FLOOR)`，A2 Cast 矩阵无 i32→i64 直达）。

与 `iterative-int-op-vector-euclid-fp32-quotient`（迭代收敛类，gcd/lcm，重点是 pass 数缩减与收敛轮询）互补：本卡针对**非迭代、固定深度**的 divmod 链，重点是偏置倒数的**可证完备单侧修正**与**无 int32 Compare/Select 约束下的纯移位修正**。偏置方向相反：迭代卡用向下偏置乘子消 r<0 分支，本卡用**向上偏置倒数** `fl((1+2^-22)/base)` 把双向偏差坍缩为单侧（q_est ∈ {q_true, q_true+1} 恒成立），只需一次 `>>31` 修正。

## 1. 原理

- **偏置倒数完备性**（数值层）：设 r = rem/base 精确实数，Q = floor(r)。`qF = fl(rem × fl((1+2^-22)/base))` 满足
  `r(1+2^-23) ≤ qF < r(1+2^-21.9)`（两级舍入误差吸收进 2^-22 偏置）。
  Q < 2^21 域内：下界 `qF ≥ Q + Q·2^-23 > Q`，上界 `qF < Q+1 + (Q+1)·2^-21.9 < Q+2` ⇒
  **trunc(qF) ∈ {Q, Q+1} 恒成立**——双向舍入偏差坍缩为单侧，修正只需处理"多商 1"一种情况。
- **单侧符号修正**（A2 约束下无比较）：A2 的向量 `Compare` 对 int32 仅支持 EQ、`Select` 仅 half/float——不能直接比较。用 `coord = rem - q·base`（q 偏大 1 时 ∈ (-base, 0)），`s = coord >> 31`（ShiftRight 算术右移，int32 得 0/-1），`q += s; coord -= s·base`。4 条指令（Muls+Add+Muls+Sub）完成修正，全程无比较无分支。
- **f32 桥接扩宽**：A2 Cast 矩阵无 `int32→int64`。坐标/索引值 < 2^24 时 float32 精确：`Cast(i32→f32, CAST_NONE) → Cast(f32→i64, CAST_FLOOR)` 两条指令精确扩宽（非负数 FLOOR == 恒等）。
- **吞吐层**：标量 `%`/`//` 每次约 20-30 cycle 且不可向量化（26k 元素/核 × K 轴 × 2 次除法 ≈ 毫秒级）；向量化后每轴 9 条指令 × (T/64) repeats，每元素 ~0.3 cycle，计算密度提升两个数量级。

## 2. 性能问题模式

1. 代码形态：kernel 内**固定次数的逐元素整数除模**（`for d: coord = rem % base; rem = rem / base`），外层逐元素标量循环 + GetValue/SetValue；被除数/模数中至少一个是编译期未知的 per-axis 常量（shape/stride/scale）。
2. 伴生形态：除模链的输入常是另一张量的逐元素值（如 index），若 `ReadXxx` 逐元素 GM 标量读，同轮一并消除（整块 DataCopyPad 进 UB + 向量 Cast 扩宽直写目标行）。
3. profiling 特征：`aiv_scalar_ratio` ≥ 0.9（本例 P3=0.984、P13=0.99），vec_ratio ≈ 0，MTE2/MTE3 < 2%；kernel 时间 ∝ nnz × ndim。
4. 逐 case 特征：nnz 越大、ndim 越深慢得越多，与 aten 向量化实现差距 5-10x。

不适用：迭代收敛型除法（次数不定，见姊妹卡）；rem/base/q 任一可能 ≥ 2^24（fp32 精确域外）；任一分母对应的商 Q=floor(rem/base) 可能 ≥ 2^21（单侧修正证明失效，须回退或改有界多次修正）；模数为逐元素非常量（倒数无法 per-axis 预计算——需改乘 magic number 表）。

## 3. 正确性红线

- **2^24 输入域 + 2^21 商域门控**：rem（≤ nnz）、每轴 base、坐标值、int32 输入值必须全部 < 2^24；同时每轴商 Q=floor(rem/base) 必须 < 2^21。证明中的单侧修正 `trunc(qF) ∈ {Q, Q+1}` 依赖 Q < 2^21；Q 超界时一次修正不能保证收敛（例如 rem=16777214、base=2 时 Q=8388607，qF=8388609，一次修正后仍余 -2）。host 端必须同时判定输入域与商域并置 fallback 标志，超界走原标量路径——不能只在 kernel 里假设。若必须覆盖 Q ≥ 2^21，需实现有界多次修正并重新证明，当前版本不包含。
- **偏置方向**：倒数必须**向上偏置**（(1+2^-22)/base，double 算好转 float 传入），若用向下偏置则 q_est ∈ {Q-1, Q}，单侧修正方向相反且 `coord ∈ [0, 2base)` 检测不了（>>31 恒 0）——方向搞反则静默错误。
- **dim/跳过轴仍需传递商**：unravel 类链中"该轴输出被外部值替换"（如 coords[dim]=index）时，**该轴的除法仍要做**（rem 链不能断），只是不产出坐标——`continue` 跳过整个轴体是典型错误（dim=0 时恰好最后 peel 轴而掩盖）。
- **修正序列槽位**：q_est 与 q·base 不能共槽（Muls 会覆盖 q_est，修正时已丢）；用已死的 ramp/临时槽存 qb 与 s·base。
- **int64 输入直拷**：dim 行来源是 int64 索引时直接 GM→UB 字节搬运落位，不过 f32 桥（int64 值域超 2^24 会丢精度）；int32 来源才走桥。
- **标量路径保留**：fallback 与向量路径共存时，UB 分配按最大需求（两路径 buffer 尺寸不同）在 Init 里按标志分派。

## 4. 泛化条件

- **适用**（任一）：固定深度逐元素整数 divmod 链（unravel/ravel、混合进制解码、多轴下标分解、scale/level 量化取整）；输出需要 int64 而计算在 int32 域（A2 无 i32→i64 Cast 的场景）；除模伴逐元素 GM 标量读（index/表驱动值），可整块搬运 + 向量 Cast 一并消除。
- **不适用**（任一）：迭代收敛型（次数不定）——用 `iterative-int-op-vector-euclid-fp32-quotient`；值域 ≥ 2^24 或每轴商 Q ≥ 2^21 且无法门控回退；模数逐元素变化（per-lane base）——需 Gather 倒数表，另案；搬运主导且计算占比 < 20%（先修搬运）。

## 5. 实施步骤

1. profiling 确认 scalar_ratio 主导 + kernel 时间 ∝ nnz×K 的固定深度除模形态。
2. host 端预计算每轴 `invBias = float((1.0 + 2.384185791015625e-07) / base)`（double 算，float 存），随 tiling 下发；同时算 2^24 输入域、每轴商 Q<2^21 判定与 fallback 标志。
3. kernel 内按轴生成向量链（见摘要），tile 内等差 p 向量用 GM 缓存 ramp 常量 + `Adds(tile 起点)` 生成，轴间 rem 用双槽 ping-pong（swap offset，零拷贝）。
4. dim/替换轴：只做除法传递不产出坐标；该行输出由 index 块搬运 + （int32 时）f32 桥 Cast 落位。
5. V→V 向量链间不加 PipeBarrier（向量单元按序）；仅 MTE↔V 边界加。
6. UB 预算：coords(K·T·8B) + 6 个 int32 工作槽 + 2 个 f32 槽（T=2048、K≤5 约 152KB < 192KB；K>5 降 T=1024）。
7. 全量精度（bit-exact）+ 双源计时回归；超界 shape 走 fallback 验证一致性。

## 6. LLM 前置问题

- 除模深度是否固定（编译期/tiling 已知 K）？每轴模数是标量常量还是逐元素张量？
- rem/base/坐标/int32 输入的值域上界各是多少？全部 < 2^24 吗？每轴商 Q=floor(rem/base) 是否 < 2^21？超界的回退路径在哪？
- 偏置方向是否向上（(1+2^-22)/base）？修正是否只用 >>31 符号掩码（未误用 int32 Compare/Select）？
- 替换轴（如 dim 行）是否仍做了 rem 除法传递？q_est 与 q·base 是否共槽？
- int64 数据行是否绕开了 f32 桥（直拷）？fallback 的 UB 分配是否按两路径最大需求？

## 7. 验收标准

- build + 精度全过；全量精度 bit-exact + 双源计时回归；超界 shape（输入域 ≥2^24 与商域 Q≥2^21 两类边界，至少覆盖 Q=2^21-1/2^21）走 fallback 验证一致性；scalar_ratio 从 ≥0.9 显著回落（本例 P3=0.984、P13=0.99 的标量主导形态消除），kernel 时间不再随 nnz×K 毫秒级增长。

## 检索卡（短卡）

动作：采用偏置倒数qF=fl(rem×fl((1+2^-22)/base))，向量化固定深度标量整数除模链。
适用：适用于固定深度逐元素整数 divmod 链，如混合进制解码或多轴下标分解。
限制：rem、各轴 base、坐标值及 int32 输入值都必须小于 2^24，且每轴商 Q 必须小于 2^21；否则回退标量路径。
范围：kernel 内固定深度的逐元素整数除模链。
检索词：divmod、混合进制、GetValue/SetValue、偏置倒数、2^24 精确域、2^21 商域
机会：Vector 单元没有整数除法原语，kernel 内仍有固定次数的逐元素整数除模。
