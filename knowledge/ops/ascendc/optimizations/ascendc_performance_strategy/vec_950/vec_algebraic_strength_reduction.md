---
type: Optimization
title: VEC 计算链代数强度削减：用单条指令复用代数恒等相关结果
description: 在 VEC-bound 的 elementwise 计算链中，若某个子表达式与其前序结果满足代数恒等（如 den = 2+2u+u^2 ≡ num+2，其中 num = u*(u+2) 已由前序指令算出），则用单条 VEC 指令（Adds）复用已有结果替代独立构建该子表达式的多指令链，削减每 repeat 的 VEC 指令数与活寄存器数。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/vec-algebraic-strength-reduction.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "VEC 指令削减量必须大于其他流水（MTE2/MTE3/scalar）的未重叠部分才能落地为时延收益；跨流水重叠充足时收益近似等于 VEC 繁忙时间下降",
      "修改必须保持 mask/tail 处理、dtype 分派、tiling 路由与同步结构不变",
      "必须重新运行完整 correctness/精度门禁，确认重结合的 ULP 差在容差内"
    ],
    "excluded_conditions": [
      "非 VEC-bound 的 shape（MTE2 带宽 bound、launch/scalar bound）：指令削减不预期转化为时延收益，仅作为 no-regression 守护",
      "要求逐位一致 / 0-ULP 舍入，或重结合可能引入灾难性抵消（不能保持 '1±ε 无抵消' 稳定形式）时不得使用",
      "形式验收要求两侧 stable 样本：当 run 的冻结 baseline performance artifact 不可变地 stable=false 时，确定性 compare gate 对任何 round 都必然返回 rejected——这是验收环境的边界，不是机制失败的证据"
    ],
    "required_conditions": [
      "kernel 热链为逐元素 RegTensor VEC 计算链，且完整 msprof 显示 VEC 为唯一关键流水（aiv_vec_ratio >= ~90%，MTE2/MTE3 在其下重叠）",
      "存在代数恒等相关的结果对：一个子表达式已由前序指令算出，另一个子表达式被独立构建且可通过恒等直接复用前者（如 den = num + 2）",
      "替换不引入新的数据依赖、同步或队列状态变化（纯流式 GM->UB->VEC->UB->GM 数据流）",
      "重结合的数值语义保持在算子精度容差内（只差数个 ULP 且保持无抵消的稳定形式），并已用全量数据验证"
    ]
  },
  "classification": "lesson",
  "created": "2026-08-23",
  "evidence": [
    {
      "comparison_sha256": "17c1f2557e53f73d3d9d621778630e604e45a8130ab1d9ea3d61fa165f6d2f37",
      "decision_sha256": "f87592ca6a52312a882602c59cf70537b08f9586b2fdfaf4d63da4df0283e224",
      "operator_class": "elementwise",
      "performance_sha256": "fbd54212bb409a59f4b360163b918a22faec5912e02ab00892ef9d113573cfd1",
      "round": 1,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "6e3e7b83e7b5a50caa5391f8e198d62f935e3af0625b659b47471acdf3c221cf",
      "verify_sha256": "fb2297528290d7582c2a6b96f3d06c02996c6cc5f79b341a415deefc4dea2829"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-bound",
      "vec-instruction-count",
      "alu-redundancy"
    ],
    "dtypes": [
      "fp16",
      "bf16"
    ],
    "pattern": "vec-algebraic-strength-reduction",
    "structure": [
      "vec-regtensor-compute-chain",
      "streaming-elementwise",
      "fp32-intermediate"
    ]
  },
  "generality": "op_class",
  "id": "L-MISH-VEC-STRENGTH-REDUCTION",
  "implementation_steps": [
    "用完整 msprof 确认瓶颈归属：aiv_vec_ratio >= 90% 且 VEC 为唯一临界流水，MTE2/MTE3 在 VEC 下重叠",
    "定位计算链中代数相关的子表达式对：后一个子表达式可由前一个结果加常数恒等直接得到（den = num + 2）",
    "用单条 VEC 指令（Adds）替换独立构建后者的多指令序列，删除变为死代码的临时 RegTensor",
    "确认新求值顺序与旧顺序只在 ULP 级别差异且保持无抵消的稳定形式，重新跑完整 correctness/精度门禁",
    "在 VEC-bound 目标 shape 上验收方向性收益，并在非目标 shape（MTE2-bound / 小 shape）上确认 no-regression"
  ],
  "intent": "削减 VEC 指令发射数（aiv_vec_ratio）以降低 VEC-bound 大 shape 的端到端时延，同时减少活 RegTensor 变量缓解寄存器压力。",
  "mechanism": "在 RegTensor VF 计算链中，先用 Adds(uP2, u, 2.0f) + Mul(num, u, uP2) 构建 num = u*(u+2)，再利用代数恒等 den ≡ num+2，以单条 AscendC::Reg::Adds(den, num, 2.0f, mask) 替代原本四条指令的 Muls(2u)/Mul(u^2)/Adds(2+2u)/Add(den) 序列，并删除由此变为死代码的三个 RegTensor<float> 临时变量（twoU/u2/denT）。fp16/bf16 每 64 元素 repeat 的 VEC 指令数由 14 降到 11，fp32 由 12 降到 9。新 den 的浮点求值顺序为 fl(fl(u*(u+2))+2)，与旧 fl(fl(fl(2u)+2)+fl(u^2)) 相差数个 ULP，二者都保持 '1±ε 无抵消' 的稳定形式（大负数 x 时 u→0、den→2、ratio→u 的路径不变）。",
  "name": "VEC 计算链代数强度削减：用单条指令复用代数恒等相关结果",
  "op": "mish",
  "operator_class": "elementwise",
  "operator_scope": "VEC-bound 的流式 elementwise compute chain（GM->UB->VEC->UB->GM，无数据复用、无跨核流量），热链用 RegTensor 在 VF 层逐条发射 VEC ALU 指令，且其中两个子表达式满足代数恒等关系",
  "principle": "VEC 流水繁忙（>=90%）且为唯一临界路径时，端到端时延近似正比于 VEC 指令发射量；两个子表达式存在代数恒等且其中一个已由前序指令算出时，独立重复计算另一个是冗余的 VEC 工作。用单条指令复用已有结果可在数值语义保持于精度容差内的前提下按每 repeat 削减指令数。指令削减是否转化为时延收益由瓶颈归属决定：仅当 VEC 是唯一临界流水且 MTE2/MTE3/scalar 在其下重叠时成立。",
  "related_anti_patterns": [],
  "risks": [
    "浮点重结合不是位等价：若精度容差收紧或存在抵消路径可能超差，必须用全量数据验证（新 den = fl(fl(u*(u+2))+2) vs 旧 fl(fl(fl(2u)+2)+fl(u^2))）",
    "若瓶颈实为 MTE2/launch/scalar 或 VEC 指令削减被跨流水重叠掩盖，指令数下降不会转化为时延收益（假设被证伪，需回退）",
    "run 级数据质量问题（冻结基线 unstable）会使正式 compare gate 永远返回 rejected，即使 round 侧所有验收条件通过；需换稳定基线 run 或修复基线后重新验收，不能在同 run 内无限重采集"
  ],
  "slug": "vec-algebraic-strength-reduction",
  "summary": "在 VEC-bound 的 elementwise 计算链中，若某个子表达式与其前序结果满足代数恒等（如 den = 2+2u+u^2 ≡ num+2，其中 num = u*(u+2) 已由前序指令算出），则用单条 VEC 指令（Adds）复用已有结果替代独立构建该子表达式的多指令链，削减每 repeat 的 VEC 指令数与活寄存器数。机制在大型 fp16/bf16 VEC-bound case 上实测稳定方向性收益（round 侧全部验收条件通过），但该 round 因 run 级验收环境（冻结基线 performance artifact 不可变地 unstable）被记录为 rejected——边界是验收环境而非机制。",
  "verification": {
    "correctness": [
      "rounds/001 verify 20/20 通过（round-1 kernel_hash 79d886b05923d88a，与 build.json kernel_after 一致；重新安装 build.json 包并指纹确认后采集）",
      "重结合的 ULP 差在精度容差内：verify 20/20 全部通过，未触发任一精度门禁"
    ],
    "performance": [
      "target VEC-bound cases 在确认的 round-1 kernel 上实测稳定方向性收益：case 4（fp16 67.1M）105.909->93.401us = 1.1339x（cv 0.028184, relative_mad 0.015139, stable=true）；case 9（bf16 49.7M）73.422->68.933us = 1.0651x（cv 0.009821, relative_mad 0.007413, stable=true）",
      "target 子集合计 179.331->162.334us = 1.1047x，improved=2，regressed=0，compare 行均为 improved",
      "注意：正式 compare gate 返回 ok=false（input_errors: 'baseline performance artifact is invalid, unstable, or incomplete'），原因是 run 的冻结基线 performance artifact 顶层 stable=false（18/20 case 不稳定）且不可变——非机制失败"
    ],
    "rollback_signals": [
      "任一正确性/精度门禁失败（新 den 重结合 ULP 差超容差）",
      "VEC-bound 目标 case 中位时延未改善或回归（指令削减未转化为 VEC 繁忙时间下降，假设被证伪）",
      "任一非目标 case 回归超过 max_case_regression 0.95",
      "run 的冻结基线 unstable 使 compare gate 永久返回 rejected 时，应更换稳定基线 run 或修复基线后重新验收，而不是在同 run 内继续重采集"
    ]
  }
}
-->

# 性能优化策略：VEC 计算链代数强度削减：用单条指令复用代数恒等相关结果

单一优化点：在 VEC-bound 的 elementwise 计算链中，若某个子表达式与其前序结果满足代数恒等（如 den = 2+2u+u^2 ≡ num+2，其中 num = u*(u+2) 已由前序指令算出），则用单条 VEC 指令（Adds）复用已有结果替代独立构建该子表达式的多指令链，削减每 repeat 的 VEC 指令数与活寄存器数。机制在大型 fp16/bf16 VEC-bound case 上实测稳定方向性收益（round 侧全部验收条件通过），但该 round 因 run 级验收环境（冻结基线 performance artifact 不可变地 unstable）被记录为 rejected——边界是验收环境而非机制。

## 1. 原理

VEC 流水繁忙（>=90%）且为唯一临界路径时，端到端时延近似正比于 VEC 指令发射量；两个子表达式存在代数恒等且其中一个已由前序指令算出时，独立重复计算另一个是冗余的 VEC 工作。用单条指令复用已有结果可在数值语义保持于精度容差内的前提下按每 repeat 削减指令数。指令削减是否转化为时延收益由瓶颈归属决定：仅当 VEC 是唯一临界流水且 MTE2/MTE3/scalar 在其下重叠时成立。

实现机制：在 RegTensor VF 计算链中，先用 Adds(uP2, u, 2.0f) + Mul(num, u, uP2) 构建 num = u*(u+2)，再利用代数恒等 den ≡ num+2，以单条 AscendC::Reg::Adds(den, num, 2.0f, mask) 替代原本四条指令的 Muls(2u)/Mul(u^2)/Adds(2+2u)/Add(den) 序列，并删除由此变为死代码的三个 RegTensor<float> 临时变量（twoU/u2/denT）。fp16/bf16 每 64 元素 repeat 的 VEC 指令数由 14 降到 11，fp32 由 12 降到 9。新 den 的浮点求值顺序为 fl(fl(u*(u+2))+2)，与旧 fl(fl(fl(2u)+2)+fl(u^2)) 相差数个 ULP，二者都保持 '1±ε 无抵消' 的稳定形式（大负数 x 时 u→0、den→2、ratio→u 的路径不变）。

## 2. 性能问题模式

- 优化目标：削减 VEC 指令发射数（aiv_vec_ratio）以降低 VEC-bound 大 shape 的端到端时延，同时减少活 RegTensor 变量缓解寄存器压力。
- 适用数据流：VEC-bound 的流式 elementwise compute chain（GM->UB->VEC->UB->GM，无数据复用、无跨核流量），热链用 RegTensor 在 VF 层逐条发射 VEC ALU 指令，且其中两个子表达式满足代数恒等关系
- Feature signature：`{"bottleneck": ["vec-bound", "vec-instruction-count", "alu-redundancy"], "dtypes": ["fp16", "bf16"], "pattern": "vec-algebraic-strength-reduction", "structure": ["vec-regtensor-compute-chain", "streaming-elementwise", "fp32-intermediate"]}`

## 3. 正确性红线

- 浮点重结合不是位等价：若精度容差收紧或存在抵消路径可能超差，必须用全量数据验证（新 den = fl(fl(u*(u+2))+2) vs 旧 fl(fl(fl(2u)+2)+fl(u^2))）
- 若瓶颈实为 MTE2/launch/scalar 或 VEC 指令削减被跨流水重叠掩盖，指令数下降不会转化为时延收益（假设被证伪，需回退）
- run 级数据质量问题（冻结基线 unstable）会使正式 compare gate 永远返回 rejected，即使 round 侧所有验收条件通过；需换稳定基线 run 或修复基线后重新验收，不能在同 run 内无限重采集

资源与硬件约束：

- VEC 指令削减量必须大于其他流水（MTE2/MTE3/scalar）的未重叠部分才能落地为时延收益；跨流水重叠充足时收益近似等于 VEC 繁忙时间下降
- 修改必须保持 mask/tail 处理、dtype 分派、tiling 路由与同步结构不变
- 必须重新运行完整 correctness/精度门禁，确认重结合的 ULP 差在容差内

## 4. 泛化条件

- 策略作用域：op_class：elementwise

适用：

- kernel 热链为逐元素 RegTensor VEC 计算链，且完整 msprof 显示 VEC 为唯一关键流水（aiv_vec_ratio >= ~90%，MTE2/MTE3 在其下重叠）
- 存在代数恒等相关的结果对：一个子表达式已由前序指令算出，另一个子表达式被独立构建且可通过恒等直接复用前者（如 den = num + 2）
- 替换不引入新的数据依赖、同步或队列状态变化（纯流式 GM->UB->VEC->UB->GM 数据流）
- 重结合的数值语义保持在算子精度容差内（只差数个 ULP 且保持无抵消的稳定形式），并已用全量数据验证

不适用：

- 非 VEC-bound 的 shape（MTE2 带宽 bound、launch/scalar bound）：指令削减不预期转化为时延收益，仅作为 no-regression 守护
- 要求逐位一致 / 0-ULP 舍入，或重结合可能引入灾难性抵消（不能保持 '1±ε 无抵消' 稳定形式）时不得使用
- 形式验收要求两侧 stable 样本：当 run 的冻结 baseline performance artifact 不可变地 stable=false 时，确定性 compare gate 对任何 round 都必然返回 rejected——这是验收环境的边界，不是机制失败的证据

## 5. 实施步骤

1. 用完整 msprof 确认瓶颈归属：aiv_vec_ratio >= 90% 且 VEC 为唯一临界流水，MTE2/MTE3 在 VEC 下重叠
2. 定位计算链中代数相关的子表达式对：后一个子表达式可由前一个结果加常数恒等直接得到（den = num + 2）
3. 用单条 VEC 指令（Adds）替换独立构建后者的多指令序列，删除变为死代码的临时 RegTensor
4. 确认新求值顺序与旧顺序只在 ULP 级别差异且保持无抵消的稳定形式，重新跑完整 correctness/精度门禁
5. 在 VEC-bound 目标 shape 上验收方向性收益，并在非目标 shape（MTE2-bound / 小 shape）上确认 no-regression

## 6. LLM 前置问题

- 目标实现是否满足：kernel 热链为逐元素 RegTensor VEC 计算链，且完整 msprof 显示 VEC 为唯一关键流水（aiv_vec_ratio >= ~90%，MTE2/MTE3 在其下重叠）？
- 目标实现是否满足：存在代数恒等相关的结果对：一个子表达式已由前序指令算出，另一个子表达式被独立构建且可通过恒等直接复用前者（如 den = num + 2）？
- 目标实现是否满足：替换不引入新的数据依赖、同步或队列状态变化（纯流式 GM->UB->VEC->UB->GM 数据流）？
- 是否命中排除条件：非 VEC-bound 的 shape（MTE2 带宽 bound、launch/scalar bound）：指令削减不预期转化为时延收益，仅作为 no-regression 守护？

## 7. 验收标准

正确性：

- rounds/001 verify 20/20 通过（round-1 kernel_hash 79d886b05923d88a，与 build.json kernel_after 一致；重新安装 build.json 包并指纹确认后采集）
- 重结合的 ULP 差在精度容差内：verify 20/20 全部通过，未触发任一精度门禁

性能：

- target VEC-bound cases 在确认的 round-1 kernel 上实测稳定方向性收益：case 4（fp16 67.1M）105.909->93.401us = 1.1339x（cv 0.028184, relative_mad 0.015139, stable=true）；case 9（bf16 49.7M）73.422->68.933us = 1.0651x（cv 0.009821, relative_mad 0.007413, stable=true）
- target 子集合计 179.331->162.334us = 1.1047x，improved=2，regressed=0，compare 行均为 improved
- 注意：正式 compare gate 返回 ok=false（input_errors: 'baseline performance artifact is invalid, unstable, or incomplete'），原因是 run 的冻结基线 performance artifact 顶层 stable=false（18/20 case 不稳定）且不可变——非机制失败

回滚信号：

- 任一正确性/精度门禁失败（新 den 重结合 ULP 差超容差）
- VEC-bound 目标 case 中位时延未改善或回归（指令削减未转化为 VEC 繁忙时间下降，假设被证伪）
- 任一非目标 case 回归超过 max_case_regression 0.95
- run 的冻结基线 unstable 使 compare gate 永久返回 rejected 时，应更换稳定基线 run 或修复基线后重新验收，而不是在同 run 内继续重采集

## 8. 分类与证据

- Classification：`lesson`
- Generality：`op_class`
- Related anti-patterns：无

- mish-20260823_153850-c81a6f（round=1, status=rejected）

## 检索卡（短卡）

动作：以单条指令复用前序已有的代数结果，替代另一子表达式的独立重复计算
适用：VEC 流水繁忙度不低于 90%，且是唯一临界路径
限制：浮点重结合非位等价；容差收紧或存在抵消路径时须全量验证
范围：elementwise-arithmetic 的逐元素 RegTensor VEC 热链
检索词：VEC、RegTensor、代数恒等、指令发射、寄存器压力
机会：两个子表达式代数恒等，且其中一个已由前序指令算出
代价：可能改变浮点位结果，并在严格容差或抵消路径中超差
