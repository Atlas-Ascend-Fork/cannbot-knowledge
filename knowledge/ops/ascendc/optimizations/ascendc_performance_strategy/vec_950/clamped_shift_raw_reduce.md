---
type: Optimization
title: 原始域 max 归约 + 溢出安全 clamped 平移，替换 reduce 扫的逐元素前处理
description: 把 reduce-max 扫的逐元素 hardswish 前处理改为对原始 x 归约，再用 Maxs 夹取得溢出安全平移 c。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/clamped-shift-raw-reduce.md
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
      "替换的合法性来自 softmax 平移不变性 + 分段上界，而不是来自位级恒等：换平移量会改变 exp 的自变量，因此该改动必然是舍入级差异，只能挂在容差型门禁（fp64 golden + MERE/MARE）上；门禁要求位精确复刻时不成立",
      "朴素同态 max(h) = h(max(x)) 被显式否决：hardswish 在 [-3,-1.5] 上非单调（x=-1.5 处取最小 -0.375，h(-3)=0 > h(-1.5)），任何依赖单调性的化简都是错的",
      "strided 路径没有 cross-lane reduce，必须就地夹取每 lane 的原始 max（ClampUbNonNeg），不能沿用 row 路径『先归约再夹取广播』的形态",
      "重建必须从干净的 kernel/build 目录开始（direction_001 的教训：增量重建以 ld.lld -Ttext 错误失败）"
    ],
    "excluded_conditions": [
      "max 归约结果被非平移用途消费时不适用：本机制的前提是 m 的唯一消费者是 Sub 之前的广播",
      "无法对原始域证明溢出安全上界（h(x) <= c）时不适用",
      "精度门要求位精确复刻、或 golden 逐元素比对不接受舍入级偏移时不适用"
    ],
    "required_conditions": [
      "存在 fused 归约把昂贵的逐元素前处理只为得到一个平移量而重复计算（本 run：max 扫对每元素算 5 条 hardswish 指令，仅为了得到 max(h)，且 m 无其它消费者）",
      "算子对平移不变（softmax/normalize 家族），归约结果可被替换为任意等价且不溢出的界",
      "可对原始输入域给出分段证明的溢出安全平移量（本 run：x>=0 时 (x+3)/6<=1（x<=3）、h=x（x>=3）；-3<x<0 时 h<0，故 h(x)<=max(x,0)，取 c=max(max_x,0) 后 exp 自变量 h-c 落在 (0,1+eps]，分母 >= exp(-0.375) > 0.69）"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-14",
  "evidence": [
    {
      "operator": "SoftmaxHardswish",
      "operator_class": "fused-composite",
      "precision": "20/20 PASS（bfloat16 6/6、float16 6/6、float32 8/8；MERE/MARE 相对 champion 为舍入级偏移，bf16 worst MARE 7.81e-3 vs 限 7.81e-2，fp32 MERE ~4.7e-8）",
      "rounds_or_pairs": "6 对均衡配对",
      "run_id": "<run-id>",
      "speedup": 1.0568,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec",
      "redundant-elementwise-prefix-in-reduce-sweep"
    ],
    "dtypes": [
      "bf16",
      "fp16",
      "fp32"
    ],
    "pattern": "clamped-shift-raw-reduce",
    "reduce_mode": "row-max",
    "structure": [
      "shift-invariance",
      "clamped-shift",
      "raw-domain-reduce",
      "piecewise-bound",
      "tolerance-not-bitwise"
    ]
  },
  "generality": "op_class",
  "id": "MISH-CLAMPED-SHIFT-RAW-REDUCE",
  "implementation_steps": [
    "在 max 扫描中用 RawMaxPass 替换 HardswishMaxPass：只做 load/upcast + lane-wise Max，不再逐元素计算 5 条 hardswish 指令",
    "把 MaxBroadcast 改为 RawMaxClampedBroadcast：广播前用一条 Maxs(red, red, 0) 夹取，得到平移 c=max(max_x,0) 写入 maxUb_",
    "新增 ClampUbNonNeg；StridedPassMax 在 strided 路径上就地夹取 per-lane 原始 max（该路径无 cross-lane reduce，夹取形态不同）",
    "sum/out 扫描保持不变，只是把收到的平移量由 m 换成 c；以分段界 h(x)<=max(x,0)<=c 保证不溢出，并显式否决 max(h)=h(max(x)) 的同态变体",
    "从干净的 kernel/build 目录重建，走容差型精度门（MERE/MARE）确认舍入级偏差在限内，再用配对 ABBA 验收性能"
  ],
  "intent": "消除 max 归约扫描中为求 max(h(x)) 而逐元素计算 hardswish 的 5 条向量指令（每元素 max 扫 7/8 条中占 5 条，全链 20/22 条中约占 1/4），把 softmax 平移量改由原始 x 的 max 夹取得到。",
  "mechanism": "clamped-shift-softmax-raw-x-reduce：champion 的 max 扫逐元素算 h=hardswish(x)（Adds(x+3)、Maxs(0)、Mins(6)、Mul、Muls(1/6)、Max）只为归约出 max(h)，而 m 唯一用途是 Sub 前的平移。本机制改为对原始 x 归约：RawMaxPass 只做 load/upcast + lane-wise Max，MaxBroadcast 在广播前用一条 Maxs(red,red,0) 夹取，得到溢出安全的平移 c=max(max_x,0)；新增 ClampUbNonNeg，StridedPassMax 在 strided 路径上就地夹取其 per-lane 原始 max。sum/out 扫描（HardswishSumExpPass / HardswishSumExpStorePass / HardswishOutPass / ExpScaleOutPass）结构完全不变，只是收到 c 而非 m。合法性由 softmax 平移不变性 + 分段界 h(x)<=max(x,0)<=c 支撑，因此输出只发生 exp 自变量层面的舍入级变化。",
  "name": "原始域 max 归约 + 溢出安全 clamped 平移，替换 reduce 扫的逐元素前处理",
  "operator_class": "fused-composite",
  "operator_scope": "带 fused 逐元素前处理 + 平移不变归一化的复合算子：前处理只为归约出一个平移量而逐元素重复计算，且可对原始域证明溢出安全上界（softmax/normalize 家族；本 run 覆盖 20 个 case：[4096,4096] dim=-1，D=4096=SH_ROW_TILE，numSt==1 走 ProcessRowsCached 快路径，另含 RowPassMax(numSt>1) 与 StridedPassMax）",
  "principle": "softmax 在实数域对平移严格不变：softmax(h,c) 与 softmax(h,m) 恒等。因此 max 扫唯一必需的是得到一个足够大又不溢出的平移量，而不必是被归约函数的真最大值。hardswish 非单调（x=-1.5 处最小），所以 max(h(x)) 与 h(max(x)) 无任何关系，朴素同态化简不成立；但对原始域有分段可证的上界：x>=0 时 h<=x<=max(x,0)，-3<x<0 时 h<0<=max(x,0)，x<=-3 时 h=0。取 c=max(max_x,0) 即得一个溢出安全且完全由原始 x 决定的替代平移，exp 自变量 h-c 落在 (0,1+eps]，分母 >= exp(-0.375) > 0.69，而全行 x<=-3 时 h=0、c=0、e=1 精确。代价是 exp 的自变量由 h-m 变为 h-c，输出只在舍入级偏移。与既有卡 max-identity-substitution 的区别：那张卡是用位级恒等式（m2=max(s) ≡ rcp1）整段消掉第二遍 max 归约、输出不变；本机制不消掉归约，而是把归约对象从变换域换回原始域，并把得到的量通过夹取改造成另一个合法平移量，因此它带来的是舍入级差异而非位精确。与 vec-frontend-instruction-diet 式微替换的区别：那里是同结构下 1-2 条指令的替换（在 SoftmaxHardswish 上已被证无收益），这里删掉的是每元素 5 条指令的整段前处理。",
  "related_anti_patterns": [
    "vec-algebraic-strength-reduction"
  ],
  "risks": [
    "非位精确是设计选择而非缺陷：exp 自变量由 m 换成 c，MERE/MARE 与 champion 有舍入级差异（bf16 worst MARE 7.81e-3 vs 限 7.81e-2；fp32 MERE ~4.7e-8），必须挂在容差型门禁上并如实披露",
    "朴素同态 max(h)=h(max(x)) 不可用：hardswish 在 [-3,-1.5] 上非单调，任何依赖单调性的紧化简都是错的；本机制只用上界 c>=h，不使用等号",
    "两条 max 路径必须都改到：row 路径（归约后 Maxs 夹取再广播）与 strided 路径（无 cross-lane reduce，就地 ClampUbNonNeg）语义需一致，漏改一处即精度失败",
    "NaN 与全负行边界：NaN lane 的 max 传播语义须与原路径一致；全行 x<=-3 时 h=0、c=0、e=1 精确，此退化情形是正确性的强校验点",
    "重建必须从干净 build 目录开始（direction_001 的增量重建 ld.lld -Ttext 失败教训）"
  ],
  "slug": "clamped-shift-raw-reduce",
  "summary": "利用 softmax 平移不变性把逐元素 hardswish 链从 reduce-max 扫描中消掉：champion 逐元素算 h=hardswish(x)（5 条 vec 指令）只为归约 max(h)，改为直接对原始 x 归约 max（load + Max），并用分段界 h(x)<=max(x,0) 取溢出安全的 clamped 平移 c=max(max_x,0)；朴素同态 max(h)=h(max(x)) 因 hardswish 非单调被显式否决。aiv_vec 45.9 -> 42.7us（bf16/fp16，-7.0%）、43.4 -> 40.7us（fp32，-6.3%），kernel geomean 53.112 -> 50.257us = 1.0568x，20/20 通过且 0 修复轮；与 champion 是舍入级差异（exp 自变量不同）而非位精确。",
  "verification": {
    "correctness": [
      "20/20 PASS（bfloat16 6/6、float16 6/6、float32 8/8），0 修复轮",
      "MERE/MARE 相对 champion 为舍入级偏移（exp 自变量用 c 而非真 max m）：worst bf16 MARE 7.81e-3 vs 限 7.81e-2，fp32 MERE ~4.7e-8",
      "分段界 h(x) <= max(x,0) <= c 保证 exp 自变量不溢出；全行 x<=-3 时 h=0、c=0、e=1 精确",
      "sum/out 扫描与 eUb 未改动，UB 预算与 champion 相同（fp32 最坏约 85KB）"
    ],
    "performance": [
      "formal 配对 6 对、相关性明确：kernel geomean 53.112 -> 50.257us = 1.0568x",
      "aiv_vec 45.9 -> 42.7us（bf16/fp16，-7.0%）与 43.4 -> 40.7us（fp32，-6.3%），memory 管处于地板",
      "退化场景：若 vec 发射行为不随被删指令数缩放，收益会向噪声压缩；被删的 5 条约占每元素 20/22 条的 1/4，完全抵消的可能性低"
    ],
    "rollback_signals": [
      "配对 ABBA 相对冻结 champion 回退，或精度失败且无可归因的性能收益",
      "MERE/MARE 超出容差门（非线性代数替换的典型失败形态）",
      "row 与 strided 两条 max 路径的夹取语义不一致",
      "从非干净 build 目录重建导致链接失败/结果不可信"
    ]
  }
}
-->

# 性能优化策略：原始域 max 归约 + 溢出安全 clamped 平移，替换 reduce 扫的逐元素前处理

利用 softmax 平移不变性把逐元素 hardswish 链从 reduce-max 扫描中消掉：改为直接对原始 x 归约 max（load + Max），并用分段界 h(x)<=max(x,0) 取溢出安全的 clamped 平移 c=max(max_x,0)；朴素同态 max(h)=h(max(x)) 因 hardswish 非单调被显式否决。kernel geomean 53.112 -> 50.257us = 1.0568x，20/20 通过且 0 修复轮；与 champion 是舍入级差异而非位精确。

## 1. 原理

softmax 在实数域对平移严格不变：softmax(h,c) 与 softmax(h,m) 恒等。因此 max 扫唯一必需的是得到一个足够大又不溢出的平移量，而不必是被归约函数的真最大值。hardswish 非单调（x=-1.5 处最小），所以 max(h(x)) 与 h(max(x)) 无任何关系，朴素同态化简不成立；但对原始域有分段可证的上界：x>=0 时 h<=x<=max(x,0)，-3<x<0 时 h<0<=max(x,0)，x<=-3 时 h=0。取 c=max(max_x,0) 即得一个溢出安全且完全由原始 x 决定的替代平移，exp 自变量 h-c 落在 (0,1+eps]，分母 >= exp(-0.375) > 0.69，而全行 x<=-3 时 h=0、c=0、e=1 精确。代价是 exp 的自变量由 h-m 变为 h-c，输出只在舍入级偏移。与既有卡 max-identity-substitution 的区别：那张卡是用位级恒等式（m2=max(s) ≡ rcp1）整段消掉第二遍 max 归约、输出不变；本机制不消掉归约，而是把归约对象从变换域换回原始域，并把得到的量通过夹取改造成另一个合法平移量，因此它带来的是舍入级差异而非位精确。与 vec-frontend-instruction-diet 式微替换的区别：那里是同结构下 1-2 条指令的替换（在 SoftmaxHardswish 上已被证无收益），这里删掉的是每元素 5 条指令的整段前处理。

实现机制：champion 的 max 扫逐元素算 h=hardswish(x)（Adds(x+3)、Maxs(0)、Mins(6)、Mul、Muls(1/6)、Max）只为归约出 max(h)，而 m 唯一用途是 Sub 前的平移。本机制改为对原始 x 归约：RawMaxPass 只做 load/upcast + lane-wise Max，MaxBroadcast 在广播前用一条 Maxs(red,red,0) 夹取，得到溢出安全的平移 c=max(max_x,0)；新增 ClampUbNonNeg，StridedPassMax 在 strided 路径上就地夹取其 per-lane 原始 max。sum/out 扫描（HardswishSumExpPass / HardswishSumExpStorePass / HardswishOutPass / ExpScaleOutPass）结构完全不变，只是收到 c 而非 m。合法性由 softmax 平移不变性 + 分段界 h(x)<=max(x,0)<=c 支撑，因此输出只发生 exp 自变量层面的舍入级变化。

## 2. 性能问题模式

- 优化目标：消除 max 归约扫描中为求 max(h(x)) 而逐元素计算 hardswish 的 5 条向量指令（每元素 max 扫 7/8 条中占 5 条，全链 20/22 条中约占 1/4），把 softmax 平移量改由原始 x 的 max 夹取得到
- 适用数据流：带 fused 逐元素前处理 + 平移不变归一化的复合算子：前处理只为归约出一个平移量而逐元素重复计算，且可对原始域证明溢出安全上界（softmax/normalize 家族；本 run 覆盖 20 个 case：[4096,4096] dim=-1，D=4096=SH_ROW_TILE，numSt==1 走 ProcessRowsCached 快路径，另含 RowPassMax(numSt>1) 与 StridedPassMax）
- Feature signature：`{"bottleneck": ["vec", "redundant-elementwise-prefix-in-reduce-sweep"], "dtypes": ["bf16", "fp16", "fp32"], "pattern": "clamped-shift-raw-reduce", "reduce_mode": "row-max", "structure": ["shift-invariance", "clamped-shift", "raw-domain-reduce", "piecewise-bound", "tolerance-not-bitwise"]}`

## 3. 正确性红线

- 非位精确是设计选择而非缺陷：exp 自变量由 m 换成 c，MERE/MARE 与 champion 有舍入级差异（bf16 worst MARE 7.81e-3 vs 限 7.81e-2；fp32 MERE ~4.7e-8），必须挂在容差型门禁上并如实披露
- 朴素同态 max(h)=h(max(x)) 不可用：hardswish 在 [-3,-1.5] 上非单调，任何依赖单调性的紧化简都是错的；本机制只用上界 c>=h，不使用等号
- 两条 max 路径必须都改到：row 路径（归约后 Maxs 夹取再广播）与 strided 路径（无 cross-lane reduce，就地 ClampUbNonNeg）语义需一致，漏改一处即精度失败
- NaN 与全负行边界：NaN lane 的 max 传播语义须与原路径一致；全行 x<=-3 时 h=0、c=0、e=1 精确，此退化情形是正确性的强校验点
- 重建必须从干净 build 目录开始（direction_001 的增量重建 ld.lld -Ttext 失败教训）

资源与硬件约束：

- 替换的合法性来自 softmax 平移不变性 + 分段上界，而不是来自位级恒等：换平移量会改变 exp 的自变量，因此该改动必然是舍入级差异，只能挂在容差型门禁（fp64 golden + MERE/MARE）上；门禁要求位精确复刻时不成立
- 朴素同态 max(h) = h(max(x)) 被显式否决：hardswish 在 [-3,-1.5] 上非单调（x=-1.5 处取最小 -0.375，h(-3)=0 > h(-1.5)），任何依赖单调性的化简都是错的
- strided 路径没有 cross-lane reduce，必须就地夹取每 lane 的原始 max（ClampUbNonNeg），不能沿用 row 路径『先归约再夹取广播』的形态
- 重建必须从干净的 kernel/build 目录开始（direction_001 的教训：增量重建以 ld.lld -Ttext 错误失败）

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- 存在 fused 归约把昂贵的逐元素前处理只为得到一个平移量而重复计算（本 run：max 扫对每元素算 5 条 hardswish 指令，仅为了得到 max(h)，且 m 无其它消费者）
- 算子对平移不变（softmax/normalize 家族），归约结果可被替换为任意等价且不溢出的界
- 可对原始输入域给出分段证明的溢出安全平移量（本 run：x>=0 时 (x+3)/6<=1（x<=3）、h=x（x>=3）；-3<x<0 时 h<0，故 h(x)<=max(x,0)，取 c=max(max_x,0) 后 exp 自变量 h-c 落在 (0,1+eps]，分母 >= exp(-0.375) > 0.69）

不适用：

- max 归约结果被非平移用途消费时不适用：本机制的前提是 m 的唯一消费者是 Sub 之前的广播
- 无法对原始域证明溢出安全上界（h(x) <= c）时不适用
- 精度门要求位精确复刻、或 golden 逐元素比对不接受舍入级偏移时不适用

## 5. 实施步骤

1. 在 max 扫描中用 RawMaxPass 替换 HardswishMaxPass：只做 load/upcast + lane-wise Max，不再逐元素计算 5 条 hardswish 指令
2. 把 MaxBroadcast 改为 RawMaxClampedBroadcast：广播前用一条 Maxs(red, red, 0) 夹取，得到平移 c=max(max_x,0) 写入 maxUb_
3. 新增 ClampUbNonNeg；StridedPassMax 在 strided 路径上就地夹取 per-lane 原始 max（该路径无 cross-lane reduce，夹取形态不同）
4. sum/out 扫描保持不变，只是把收到的平移量由 m 换成 c；以分段界 h(x)<=max(x,0)<=c 保证不溢出，并显式否决 max(h)=h(max(x)) 的同态变体
5. 从干净的 kernel/build 目录重建，走容差型精度门（MERE/MARE）确认舍入级偏差在限内，再用配对 ABBA 验收性能

## 6. LLM 前置问题

- 目标实现是否满足：存在 fused 归约把昂贵的逐元素前处理只为得到一个平移量而重复计算（本 run：max 扫对每元素算 5 条 hardswish 指令，仅为了得到 max(h)，且 m 无其它消费者）？
- 目标实现是否满足：算子对平移不变（softmax/normalize 家族），归约结果可被替换为任意等价且不溢出的界？
- 目标实现是否满足：可对原始输入域给出分段证明的溢出安全平移量（本 run：x>=0 时 (x+3)/6<=1（x<=3）、h=x（x>=3）；-3<x<0 时 h<0，故 h(x)<=max(x,0)，取 c=max(max_x,0) 后 exp 自变量 h-c 落在 (0,1+eps]，分母 >= exp(-0.375) > 0.69）？
- 是否命中排除条件：max 归约结果被非平移用途消费时不适用？
- 是否命中排除条件：无法对原始域证明溢出安全上界（h(x) <= c）时不适用？
- 是否命中排除条件：精度门要求位精确复刻、或 golden 逐元素比对不接受舍入级偏移时不适用？

## 7. 验收标准

正确性：

- 20/20 PASS（bfloat16 6/6、float16 6/6、float32 8/8），0 修复轮
- MERE/MARE 相对 champion 为舍入级偏移（exp 自变量用 c 而非真 max m）：worst bf16 MARE 7.81e-3 vs 限 7.81e-2，fp32 MERE ~4.7e-8
- 分段界 h(x) <= max(x,0) <= c 保证 exp 自变量不溢出；全行 x<=-3 时 h=0、c=0、e=1 精确
- sum/out 扫描与 eUb 未改动，UB 预算与 champion 相同（fp32 最坏约 85KB）

性能：

- formal 配对 6 对、相关性明确：kernel geomean 53.112 -> 50.257us = 1.0568x
- aiv_vec 45.9 -> 42.7us（bf16/fp16，-7.0%）与 43.4 -> 40.7us（fp32，-6.3%），memory 管处于地板
- 退化场景：若 vec 发射行为不随被删指令数缩放，收益会向噪声压缩；被删的 5 条约占每元素 20/22 条的 1/4，完全抵消的可能性低

回滚信号：

- 配对 ABBA 相对冻结 champion 回退，或精度失败且无可归因的性能收益
- MERE/MARE 超出容差门（非线性代数替换的典型失败形态）
- row 与 strided 两条 max 路径的夹取语义不一致
- 从非干净 build 目录重建导致链接失败/结果不可信

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：vec-algebraic-strength-reduction

- loop_20260913_070917（status=accepted, speedup=1.0568, precision=20/20 PASS（bfloat16 6/6、float16 6/6、float32 8/8；MERE/MARE 相对 champion 为舍入级偏移，bf16 worst MARE 7.81e-3 vs 限 7.81e-2，fp32 MERE ~4.7e-8））

## 检索卡（短卡）

动作：把 reduce-max 扫的逐元素 hardswish 前处理改为对原始 x 归约，再用 Maxs 夹取得溢出安全平移 c
适用：算子对平移不变（softmax/normalize 家族），且可对原始域证明上界 h(x)<=max(x,0)
限制：非位精确须挂容差门禁；row 与 strided 两条 max 路径须一致；同态 max(h)=h(max(x)) 因非单调被否决
范围：fused-composite 的 fused 逐元素前处理 + 平移不变归一化
检索词：RawMaxPass、Maxs 夹取、ClampUbNonNeg、StridedPassMax、平移不变性
机会：max 扫每元素算 5 条 hardswish 只为归约 max(h)
代价：exp 自变量由 h-m 变 h-c，与 champion 舍入级差异，须在门禁披露
