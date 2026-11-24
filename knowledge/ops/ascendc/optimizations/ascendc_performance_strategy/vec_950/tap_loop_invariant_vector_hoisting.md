---
type: Optimization
title: tap 循环不变量向量外提 + 编译期 kW 模板特化
description: 把 tap 循环内反复重建的向量不变量外提为寄存器常驻 per-(row,chunk) 前导，并以编译期 kW 模板特化分派。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/tap-loop-invariant-vector-hoisting.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-20T06:35:03Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "kW 必须走编译期模板特化（ComputeRow 的 switch(kW){1,2,3,4} 分派到 AccumulateRowsHoisted<KW>），不得用运行期守卫展开——round_01 的运行期守卫版本在 kW=4 case 上因额外 vec 负载与寄存器压力回退（case3 +6.5%、case20 +4.0%）并在该方向内回滚",
      "kW>4 保留原 AccumulateRow + ResetAccumulator 遗留路径，特化只覆盖有界的取值域（本 run 1..4）",
      "可外提的量必须是 (W,kW,sW,pW,chunkStart,lanes) 的函数（每 chunk 构造一次）；随 tap/k 变化的量不得外提，否则不再是同一计算结果",
      "gather 下标、有效性掩码、zero 寄存器、tap/k 访问顺序与除数路径必须全部不变，否则位级一致性不成立"
    ],
    "excluded_conditions": [
      "kW>4 时无特化路径，本机制不适用（回退遗留路径）",
      "tap 体成本不由标量发射/重复向量构造主导时不适用：收益来自削减 aiv_scalar 发射与重复的向量构造工作",
      "kW 取值域无法在编译期枚举时不适用（无法模板特化）"
    ],
    "required_conditions": [
      "存在逐 (output row x valid kD*kH tap x Wout chunk) 重复构造、但只依赖 (W,kW,sW,pW,chunkStart,lanes) 的向量不变量（本 run：tap 下标向量 Arange+Muls+Adds、逐 k 有效性掩码 2x CompareScalar+And、夹取后的 gather 下标 Move+Maxs+Mins、zero 寄存器与逐 k Select）",
      "标量管是主绑定管（本 run 冻结基线 screening geomean 36.666us，bf16 34.363 / fp16 45.977 / fp32 31.201，每个 dtype 组都由 scalar 管定速）",
      "编译期 kW 取值域小且有界（本 run kW<=4 覆盖全部目标 case）",
      "输出对 tap 访问顺序与 gather 下标敏感，因此要求位级一致的验收方式（逐 case MERE/MARE 与冻结基线逐字节一致）"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-14",
  "evidence": [
    {
      "operator": "avgpool3d",
      "operator_class": "pool3d",
      "precision": "18/20 基线一致性 PASS（失败集 {11,12} bad=0 为 pre-existing inf-overflow comparator 限制，pre-loop 原版与所有基线一致；20 个 case 逐 case MERE/MARE 与冻结基线逐字节相同）",
      "rounds_or_pairs": "40/40 逐 case 配对测量（20 case x 2 对）",
      "run_id": "<run-id>",
      "speedup": 1.1535,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-pipe",
      "repeated-invariant-vector-construction",
      "scalar-emission-count"
    ],
    "dtypes": [
      "bf16",
      "fp16",
      "fp32"
    ],
    "pattern": "tap-loop-invariant-vector-hoisting",
    "reduce_mode": "window-sum",
    "structure": [
      "cross-tap-invariant-hoisting",
      "register-resident-invariants",
      "compile-time-kw-template-specialization",
      "legacy-path-above-kw4",
      "bitwise-identical-outputs"
    ]
  },
  "generality": "op_class",
  "id": "POOL3D-TAP-LOOP-INVARIANT-HOIST",
  "implementation_steps": [
    "在 AvgPool3dRegImpl 增加 AccumulateRowsHoisted<KW> 模板：每 (row, chunk) 只构造一次 tap 下标基（Arange+Muls+Adds）、逐 k 夹取后的 gather 下标寄存器 g0..g3（Move+Maxs+Mins）、逐 k 有效性掩码 m0..m3（2x CompareScalar+And）、zero 寄存器与零初始化累加器",
    "把 tap 循环体收缩为 KW x (Gather+Select+Add)，累加器保持寄存器常驻，chunk 末只做一次 StoreAlign",
    "ComputeRow 用 switch(kW){1,2,3,4} 分派到编译期特化（无逐 tap 运行期分支，寄存器活跃集精确）；kW>4 保留原 AccumulateRow + ResetAccumulator",
    "保持 gather 下标、掩码、zero、tap/k 访问顺序与除数路径不变，用逐 case MERE/MARE 与冻结基线逐字节一致来验证位级相同",
    "用配对 ABBA 确认所有 dtype 组同向改善且无回退 case，任一 dtype 组或 case 回退即回滚"
  ],
  "intent": "消除 W-tap 累加中逐 (row x tap x chunk) 重复构造不变量的成本：tap 下标向量、逐 k 有效性掩码、夹取后的 gather 下标、zero 寄存器与逐 k Select 被反复重建，主导了 aiv_scalar 发射量并附带大量冗余的向量 Compare/And/Mins/Maxs/Move/Select。",
  "mechanism": "cross-tap-invariant-index-mask-hoisting：AccumulateRow 每个 (output row x valid kD*kH tap x Wout chunk) 都重建只依赖 (W,kW,sW,pW,chunkStart,lanes) 的量。新增 AvgPool3dRegImpl::AccumulateRowsHoisted<KW> 模板，per (row, chunk) 只构造一次：tap 下标基（Arange+Muls+Adds）、逐 k 夹取后的 gather 下标寄存器 g0..g3（Move+Maxs+Mins）、逐 k 有效性掩码 m0..m3（2x CompareScalar+And）、zero 寄存器与零初始化累加器；tap 循环体因此只剩 KW x (Gather+Select+Add)，累加器留在寄存器，chunk 末一次 StoreAlign。实现的关键另一半是编译期 kW 模板特化：ComputeRow 用 switch(kW){1,2,3,4} 分派，避免逐 tap 运行期分支并让寄存器活跃集精确；kW>4 保留原 AccumulateRow + ResetAccumulator 遗留路径。数值上与 champion 位级相同（同 gather 下标、同掩码、同 zero、同 tap/k 访问顺序、同除数路径）。",
  "name": "tap 循环不变量向量外提 + 编译期 kW 模板特化",
  "operator_class": "pool3d",
  "operator_scope": "逐 (row x tap x chunk) 调用累加子程序、且子程序内部重建只依赖 (W,kW,sW,pW,chunkStart,lanes) 的向量不变量的池化/窗口类算子；kW 取值域小到可编译期枚举（本 run avgpool3d，kW in {1,2,3,4} 覆盖全部目标 case，kW>4 走遗留路径）",
  "principle": "这类 kernel 的标量管成本有两层：一是逐 tap 的标量发射次数本身，二是每次发射携带的向量构造工作（下标、掩码、夹取、Select）。不变量只在 (W,kW,sW,pW,chunkStart,lanes) 上变化，而这个元组的取值数等于 chunk 数乘以行数，远小于 tap 调用次数（每次调用乘以 kD*kH）。把它们提到 tap 循环之外、以寄存器常驻形式复用，等于把 O(rows x taps x chunks) 次构造降为 O(rows x chunks) 次，tap 体收缩为纯数据路径。为什么必须编译期特化而不是运行期守卫展开：守卫展开会在循环内引入额外的 vec 负载（判断与路径分叉）与更长的活跃区间，寄存器压力上升，在 kW 较大的 case 上反而把 vec 管拖慢——这与既有卡 covh-init-precompute-ub-resident 的区别就在这里：那张卡把不变量提升为 Init 期一次生成、整 kernel 生存期的 UB 常驻表（存储类为 UB、生存期为整个 kernel、有容量守卫）；本机制的不变量是寄存器常驻、生存期仅为一个 (row, chunk) 的 tap 循环（存储类为寄存器、无需容量守卫），因此不适用于需要跨 batch 复用的量，也不引入 UB 预算变化。",
  "related_anti_patterns": [
    "flat-zone-coordinate-hoist-load-latency-bound"
  ],
  "risks": [
    "round_01 的运行期守卫展开版本（v1）被回滚：kW=2 giants 改善 10-11%，但两个 kW=4 case 在 vec 管上回退（case3 +6.5%、case20 +4.0%）；round_02 改为编译期 kW 模板特化（v2）后回退消失",
    "验收标准是基线一致性而非绝对 20/20：champion 的精度签名是 18/20，失败集 {11,12} bad=0 为 pre-existing inf-overflow comparator 限制，在 pre-loop 原版与所有 round 基线中一致",
    "位级一致性依赖 tap/k 访问顺序、gather 下标、掩码与除数路径全部不变；外提改变其中任一项即不再是同一计算结果",
    "外提后寄存器常驻量（g0..g3 / m0..m3 / zero / 累加器）增加寄存器压力，kW 较大时可能 spill，这是编译期特化必须比运行期版本更省的原因",
    "kW>4 的场景没有特化路径，回退遗留实现，收益不适用"
  ],
  "slug": "tap-loop-invariant-vector-hoisting",
  "summary": "把每条 tap/每行的向量构造工作（tap 下标 Arange+Muls+Adds、逐 k 有效性掩码 2x CompareScalar+And、夹取后的 gather 下标 Move+Maxs+Mins、zero 寄存器与逐 k Select）从 kD*kH tap 循环中提出去，变成寄存器常驻的 per-(row,chunk) 前导，tap 体只剩 kW x (Gather+Select+Add) 加一个寄存器累加器；另一半是编译期 kW 模板特化（round_01 的运行期守卫展开版本在 kW=4 上回退被回滚）。msprof device Task Duration geomean 34.572 -> 29.971us = 1.1535x（bf16 1.250x、fp32 1.138x、fp16 1.078x），输出与基线位级相同。",
  "verification": {
    "correctness": [
      "18/20 基线一致性 PASS（失败集 {11,12} bad=0 为 pre-existing inf-overflow comparator 限制，pre-loop 原版与所有基线一致）",
      "20 个 case 的逐 case MERE/MARE 与冻结基线逐字节相同（v1 与 v2 两轮皆然）→ 输出位级相同",
      "gather 下标、掩码、zero、tap/k 访问顺序与除数路径未改动"
    ],
    "performance": [
      "正式配对：msprof device Task Duration geomean 34.572 -> 29.971us = 1.1535x（bf16 1.250x、fp32 1.138x、fp16 1.078x）",
      "40/40 逐 case 配对测量不劣于候选或在噪声内，两个配对中每个 dtype 组都改善，配对间 speedup 差 0.001",
      "冻结基线新采 msprof screening geomean 36.666us（bf16 34.363 / fp16 45.977 / fp32 31.201），各 dtype 组均由 scalar 管定速",
      "round_01 v1 的 kW=4 回退（case3 +6.5%、case20 +4.0%）在 v2 特化版本中消失，v2 screening geomean 31.681us 无 dtype 回退"
    ],
    "rollback_signals": [
      "任一 dtype 组或任一 case 在配对测量上回退",
      "kW=4 等较大 kW case 出现 vec 管回退（round_01 的运行期守卫展开形态）",
      "逐 case MERE/MARE 不再与冻结基线逐字节一致",
      "外提后出现寄存器 spill 或编译期特化实例化失败"
    ]
  }
}
-->

# 性能优化策略：tap 循环不变量向量外提 + 编译期 kW 模板特化

把每条 tap/每行的向量构造工作（tap 下标、逐 k 有效性掩码、夹取后的 gather 下标、zero 寄存器与逐 k Select）从 kD*kH tap 循环中提出去，变成寄存器常驻的 per-(row,chunk) 前导，tap 体只剩 kW x (Gather+Select+Add) 加一个寄存器累加器；另一半是编译期 kW 模板特化（round_01 的运行期守卫展开版本在 kW=4 上回退被回滚）。msprof device Task Duration geomean 34.572 -> 29.971us = 1.1535x，输出与基线位级相同。

## 1. 原理

这类 kernel 的标量管成本有两层：一是逐 tap 的标量发射次数本身，二是每次发射携带的向量构造工作（下标、掩码、夹取、Select）。不变量只在 (W,kW,sW,pW,chunkStart,lanes) 上变化，而这个元组的取值数等于 chunk 数乘以行数，远小于 tap 调用次数（每次调用乘以 kD*kH）。把它们提到 tap 循环之外、以寄存器常驻形式复用，等于把 O(rows x taps x chunks) 次构造降为 O(rows x chunks) 次，tap 体收缩为纯数据路径。为什么必须编译期特化而不是运行期守卫展开：守卫展开会在循环内引入额外的 vec 负载（判断与路径分叉）与更长的活跃区间，寄存器压力上升，在 kW 较大的 case 上反而把 vec 管拖慢——这与既有卡 covh-init-precompute-ub-resident 的区别就在这里：那张卡把不变量提升为 Init 期一次生成、整 kernel 生存期的 UB 常驻表（存储类为 UB、生存期为整个 kernel、有容量守卫）；本机制的不变量是寄存器常驻、生存期仅为一个 (row, chunk) 的 tap 循环（存储类为寄存器、无需容量守卫），因此不适用于需要跨 batch 复用的量，也不引入 UB 预算变化。

实现机制：AccumulateRow 每个 (output row x valid kD*kH tap x Wout chunk) 都重建只依赖 (W,kW,sW,pW,chunkStart,lanes) 的量。新增 AvgPool3dRegImpl::AccumulateRowsHoisted<KW> 模板，per (row, chunk) 只构造一次：tap 下标基（Arange+Muls+Adds）、逐 k 夹取后的 gather 下标寄存器 g0..g3（Move+Maxs+Mins）、逐 k 有效性掩码 m0..m3（2x CompareScalar+And）、zero 寄存器与零初始化累加器；tap 循环体因此只剩 KW x (Gather+Select+Add)，累加器留在寄存器，chunk 末一次 StoreAlign。实现的关键另一半是编译期 kW 模板特化：ComputeRow 用 switch(kW){1,2,3,4} 分派，避免逐 tap 运行期分支并让寄存器活跃集精确；kW>4 保留原 AccumulateRow + ResetAccumulator 遗留路径。数值上与 champion 位级相同（同 gather 下标、同掩码、同 zero、同 tap/k 访问顺序、同除数路径）。

## 2. 性能问题模式

- 优化目标：消除 W-tap 累加中逐 (row x tap x chunk) 重复构造不变量的成本：tap 下标向量、逐 k 有效性掩码、夹取后的 gather 下标、zero 寄存器与逐 k Select 被反复重建，主导了 aiv_scalar 发射量并附带大量冗余的向量 Compare/And/Mins/Maxs/Move/Select
- 适用数据流：逐 (row x tap x chunk) 调用累加子程序、且子程序内部重建只依赖 (W,kW,sW,pW,chunkStart,lanes) 的向量不变量的池化/窗口类算子；kW 取值域小到可编译期枚举（本 run avgpool3d，kW in {1,2,3,4} 覆盖全部目标 case，kW>4 走遗留路径）
- Feature signature：`{"bottleneck": ["scalar-pipe", "repeated-invariant-vector-construction", "scalar-emission-count"], "dtypes": ["bf16", "fp16", "fp32"], "pattern": "tap-loop-invariant-vector-hoisting", "reduce_mode": "window-sum", "structure": ["cross-tap-invariant-hoisting", "register-resident-invariants", "compile-time-kw-template-specialization", "legacy-path-above-kw4", "bitwise-identical-outputs"]}`

## 3. 正确性红线

- round_01 的运行期守卫展开版本（v1）被回滚：kW=2 giants 改善 10-11%，但两个 kW=4 case 在 vec 管上回退（case3 +6.5%、case20 +4.0%）；round_02 改为编译期 kW 模板特化（v2）后回退消失
- 验收标准是基线一致性而非绝对 20/20：champion 的精度签名是 18/20，失败集 {11,12} bad=0 为 pre-existing inf-overflow comparator 限制，在 pre-loop 原版与所有 round 基线中一致
- 位级一致性依赖 tap/k 访问顺序、gather 下标、掩码与除数路径全部不变；外提改变其中任一项即不再是同一计算结果
- 外提后寄存器常驻量（g0..g3 / m0..m3 / zero / 累加器）增加寄存器压力，kW 较大时可能 spill，这是编译期特化必须比运行期版本更省的原因
- kW>4 的场景没有特化路径，回退遗留实现，收益不适用

资源与硬件约束：

- kW 必须走编译期模板特化（ComputeRow 的 switch(kW){1,2,3,4} 分派到 AccumulateRowsHoisted<KW>），不得用运行期守卫展开——round_01 的运行期守卫版本在 kW=4 case 上因额外 vec 负载与寄存器压力回退（case3 +6.5%、case20 +4.0%）并在该方向内回滚
- kW>4 保留原 AccumulateRow + ResetAccumulator 遗留路径，特化只覆盖有界的取值域（本 run 1..4）
- 可外提的量必须是 (W,kW,sW,pW,chunkStart,lanes) 的函数（每 chunk 构造一次）；随 tap/k 变化的量不得外提，否则不再是同一计算结果
- gather 下标、有效性掩码、zero 寄存器、tap/k 访问顺序与除数路径必须全部不变，否则位级一致性不成立

## 4. 泛化条件

- 策略作用域：op_class：pool3d

适用：

- 存在逐 (output row x valid kD*kH tap x Wout chunk) 重复构造、但只依赖 (W,kW,sW,pW,chunkStart,lanes) 的向量不变量（本 run：tap 下标向量 Arange+Muls+Adds、逐 k 有效性掩码 2x CompareScalar+And、夹取后的 gather 下标 Move+Maxs+Mins、zero 寄存器与逐 k Select）
- 标量管是主绑定管（本 run 冻结基线 screening geomean 36.666us，bf16 34.363 / fp16 45.977 / fp32 31.201，每个 dtype 组都由 scalar 管定速）
- 编译期 kW 取值域小且有界（本 run kW<=4 覆盖全部目标 case）
- 输出对 tap 访问顺序与 gather 下标敏感，因此要求位级一致的验收方式（逐 case MERE/MARE 与冻结基线逐字节一致）

不适用：

- kW>4 时无特化路径，本机制不适用（回退遗留路径）
- tap 体成本不由标量发射/重复向量构造主导时不适用：收益来自削减 aiv_scalar 发射与重复的向量构造工作
- kW 取值域无法在编译期枚举时不适用（无法模板特化）

## 5. 实施步骤

1. 在 AvgPool3dRegImpl 增加 AccumulateRowsHoisted<KW> 模板：每 (row, chunk) 只构造一次 tap 下标基（Arange+Muls+Adds）、逐 k 夹取后的 gather 下标寄存器 g0..g3（Move+Maxs+Mins）、逐 k 有效性掩码 m0..m3（2x CompareScalar+And）、zero 寄存器与零初始化累加器
2. 把 tap 循环体收缩为 KW x (Gather+Select+Add)，累加器保持寄存器常驻，chunk 末只做一次 StoreAlign
3. ComputeRow 用 switch(kW){1,2,3,4} 分派到编译期特化（无逐 tap 运行期分支，寄存器活跃集精确）；kW>4 保留原 AccumulateRow + ResetAccumulator
4. 保持 gather 下标、掩码、zero、tap/k 访问顺序与除数路径不变，用逐 case MERE/MARE 与冻结基线逐字节一致来验证位级相同
5. 用配对 ABBA 确认所有 dtype 组同向改善且无回退 case，任一 dtype 组或 case 回退即回滚

## 6. LLM 前置问题

- 目标实现是否满足：存在逐 (output row x valid kD*kH tap x Wout chunk) 重复构造、但只依赖 (W,kW,sW,pW,chunkStart,lanes) 的向量不变量（本 run：tap 下标向量 Arange+Muls+Adds、逐 k 有效性掩码 2x CompareScalar+And、夹取后的 gather 下标 Move+Maxs+Mins、zero 寄存器与逐 k Select）？
- 目标实现是否满足：标量管是主绑定管（本 run 冻结基线 screening geomean 36.666us，bf16 34.363 / fp16 45.977 / fp32 31.201，每个 dtype 组都由 scalar 管定速）？
- 目标实现是否满足：编译期 kW 取值域小且有界（本 run kW<=4 覆盖全部目标 case）？
- 目标实现是否满足：输出对 tap 访问顺序与 gather 下标敏感，因此要求位级一致的验收方式（逐 case MERE/MARE 与冻结基线逐字节一致）？
- 是否命中排除条件：kW>4 时无特化路径，本机制不适用（回退遗留路径）？
- 是否命中排除条件：tap 体成本不由标量发射/重复向量构造主导时不适用？
- 是否命中排除条件：kW 取值域无法在编译期枚举时不适用（无法模板特化）？

## 7. 验收标准

正确性：

- 18/20 基线一致性 PASS（失败集 {11,12} bad=0 为 pre-existing inf-overflow comparator 限制，pre-loop 原版与所有基线一致）
- 20 个 case 的逐 case MERE/MARE 与冻结基线逐字节相同（v1 与 v2 两轮皆然）→ 输出位级相同
- gather 下标、掩码、zero、tap/k 访问顺序与除数路径未改动

性能：

- 正式配对：msprof device Task Duration geomean 34.572 -> 29.971us = 1.1535x（bf16 1.250x、fp32 1.138x、fp16 1.078x）
- 40/40 逐 case 配对测量不劣于候选或在噪声内，两个配对中每个 dtype 组都改善，配对间 speedup 差 0.001
- 冻结基线新采 msprof screening geomean 36.666us（bf16 34.363 / fp16 45.977 / fp32 31.201），各 dtype 组均由 scalar 管定速
- round_01 v1 的 kW=4 回退（case3 +6.5%、case20 +4.0%）在 v2 特化版本中消失，v2 screening geomean 31.681us 无 dtype 回退

回滚信号：

- 任一 dtype 组或任一 case 在配对测量上回退
- kW=4 等较大 kW case 出现 vec 管回退（round_01 的运行期守卫展开形态）
- 逐 case MERE/MARE 不再与冻结基线逐字节一致
- 外提后出现寄存器 spill 或编译期特化实例化失败

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：flat-zone-coordinate-hoist-load-latency-bound

- loop_20260913_124740（round=2, status=accepted, speedup=1.1535, precision=18/20 基线一致性 PASS（失败集 {11,12} bad=0 为 pre-existing inf-overflow comparator 限制；20 个 case 逐 case MERE/MARE 与冻结基线逐字节相同））

## 检索卡（短卡）

动作：把 tap 循环内反复重建的向量不变量外提为寄存器常驻 per-(row,chunk) 前导，并以编译期 kW 模板特化分派。
适用：存在只依赖 (W,kW,sW,pW,chunkStart,lanes)、却在每 tap 重复构造的向量不变量。
限制：kW 须编译期模板特化，不得用运行期守卫展开（kW=4 上回退）；kW>4 走遗留路径；gather 下标/掩码/zero/访问顺序不变。
范围：逐 (row x tap x chunk) 调用累加子程序的池化/窗口算子
检索词：AccumulateRowsHoisted、Arange+Muls+Adds、Move+Maxs+Mins、Gather+Select+Add
机会：tap 下标、有效性掩码、夹取后 gather 下标与 zero 被反复重建
代价：寄存器常驻量增加压力，kW 大时可能 spill
