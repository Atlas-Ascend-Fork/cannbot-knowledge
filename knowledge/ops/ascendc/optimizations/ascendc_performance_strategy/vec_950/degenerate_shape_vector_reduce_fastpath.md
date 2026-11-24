---
type: Optimization
title: 退化归约的向量化快路径
description: 识别退化归约形状，用向量累加器和分层树归约替代标量串行循环。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/degenerate-shape-vector-reduce-fastpath.md
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
      "每一级树归约的源/目标地址都必须满足向量 API 对齐要求，小于最小对齐跨度时改用安全收尾",
      "尾 chunk 只能读取有效元素或有明确 guard 区，禁止依赖越界向量读取"
    ],
    "excluded_conditions": [
      "输出仍包含大量独立段、索引映射不规则或归约顺序具有强语义约束时应使用通用路径",
      "目标 dtype 需要更高精度累加但片上资源无法容纳提升后的累加器时不适用"
    ],
    "required_conditions": [
      "host 能从 shape 和 axis 证明输出元素数很小，且被归约数据在当前视图中可连续或规则分段访问",
      "归约算子存在可向量化的结合形式，并能为尾块提供合法 mask",
      "累加器和中间树归约缓冲满足 UB、寄存器及对齐限制"
    ]
  },
  "applicability_boundary": "",
  "classification": "validated_strategy",
  "created": "2026-08-21",
  "evidence": [
    {
      "after_us": 18.6,
      "before_us": 56852.0,
      "case": "15",
      "operator_class": "scatter-update",
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "source_report": "<PERF_ROOT>/strategies/unsorted_segment_sum_opt_20260820.md",
      "speedup": 3055.6,
      "status": "accepted"
    },
    {
      "after_us": 421.6,
      "before_us": 1370.2,
      "case": "1",
      "operator_class": "sort-select",
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "source_report": "<PERF_ROOT>/AscendSearch/.ksearch-perf-strategy-extraction/arg_max/<run-id>/phase6_apply/final_report.md",
      "speedup": 3.25,
      "status": "accepted"
    },
    {
      "comparison_sha256": "be11a7dc6d8872829d804330bca01843717e43a4c621817f2a0a18634d940b50",
      "decision_sha256": "72d0fd84401e323ce691b2351547f01fdec73bab2b4da3596a3d5047936a9eb6",
      "operator_class": "",
      "performance_sha256": "e3420a65432184aa4a84466cfda4d1f65ec0a09c7fd03016e4b74264cf804a24",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "ebcc1dad150ed38720344ac555e08b874d9fbbfe2d513a94776a5e050799f3ec",
      "verify_sha256": "65b98d4c15a6cc851689c8e80dec7e63b82906f27fc9aa79f4244bfcd05e50f1"
    },
    {
      "comparison_sha256": "1562a609eff06fbe93178565d215151ea7818481671eb1b7bb43cc25f70b2dc6",
      "decision_sha256": "df99248f33c3eaee33f91bb54eb1dab295f318a0f79780ff9f76280ba47bb4f8",
      "operator_class": "",
      "performance_sha256": "a3d00b739c14671b72b0d3aa619af6c0fe2b33e7bf557d665fbb0b17f6ed9b00",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "edafacfaf586ddbf35c73b188f32bb0b6c8600765241867051fb0080e45fb2e5",
      "verify_sha256": "36c3e4e268cf2ee65c4ff6e8931f3642436bbcf3e9ce34d2aa0f1de25f6c0e58"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-serial",
      "degenerate-shape"
    ],
    "dtypes": [],
    "pattern": "degenerate-shape-fastpath",
    "reduce_mode": "row-reduce",
    "structure": [
      "degenerate-shape",
      "vector-reduce",
      "tree-reduce"
    ]
  },
  "gain": "退化全归约 case_15 3055.6x；ArgMax 向量极值归约锚点 3.25x。",
  "generality": "common",
  "id": "S5",
  "implementation_steps": [
    "在 host 侧规范化 axis 并计算输出元素数，为可证明的退化形状设置独立 tiling key",
    "按向量宽度连续读取输入并累加到多个 lane，尾 chunk 使用精确 mask",
    "在 UB 或寄存器内分层折半归约，只有满足对齐的层级使用向量指令",
    "对最后少量 lane 使用受控的标量收尾或专用归约指令",
    "非退化 shape、非连续布局和不支持 dtype 回退到通用归约"
  ],
  "instance_ids": [],
  "intent": "退化形状（全归约）的向量快路径",
  "mechanism": "128-lane 累加器逐 128 元素一条向量 Add（尾 chunk 掩码 count）→ 树归约折半 Add（stride≥8 才 32B 对齐，否则设备 error 507035）→ 末 8 lane 标量求和。",
  "name": "退化归约的向量化快路径",
  "op": "seed",
  "operator_class": "",
  "operator_scope": "一个或多个逻辑轴退化后，通用多阶段归约变为单输出或极少输出的归约路径",
  "principle": "通用归约通常为任意输出形状保留索引映射、分块和中间写回；当输出退化为极少元素时，这些控制成本可以被专用的连续向量累加与片上树归约完全绕过。",
  "provenance": {
    "skill": "SKILL.md §7 S5"
  },
  "related_anti_patterns": [],
  "related_seed_ids": [],
  "risks": [
    "退化条件判定过宽会遗漏输出段或混合不同归约域",
    "树归约后段的非对齐地址及尾部全向量读取可能触发设备异常"
  ],
  "schema_version": 2,
  "slug": "degenerate-shape-vector-reduce-fastpath",
  "source": "skill",
  "status": "applied",
  "summary": "识别退化归约形状，用向量累加器和分层树归约替代标量串行循环。",
  "verification": {
    "correctness": [
      "覆盖空输入、单元素、刚好一个向量、非整向量尾部、极大归约长度和不同 axis 组合",
      "按算子契约验证 NaN、Inf、溢出及高精度累加行为"
    ],
    "performance": [
      "比较退化与非退化多组形状，确认标量循环、中间 GM 写回和通用索引开销消失且回退路径无回归"
    ],
    "rollback_signals": [
      "出现 axis 误判、尾部越界、对齐异常、精度漂移或非退化路径误命中时回退"
    ]
  }
}
-->

# 性能优化策略：退化归约的向量化快路径

单一优化点：识别退化归约形状，用向量累加器和分层树归约替代标量串行循环。

## 1. 原理

通用归约通常为任意输出形状保留索引映射、分块和中间写回；当输出退化为极少元素时，这些控制成本可以被专用的连续向量累加与片上树归约完全绕过。

实现机制：128-lane 累加器逐 128 元素一条向量 Add（尾 chunk 掩码 count）→ 树归约折半 Add（stride≥8 才 32B 对齐，否则设备 error 507035）→ 末 8 lane 标量求和。

## 2. 性能问题模式

- 优化目标：退化形状（全归约）的向量快路径
- 适用数据流：一个或多个逻辑轴退化后，通用多阶段归约变为单输出或极少输出的归约路径
- Feature signature：`{"bottleneck": ["scalar-serial", "degenerate-shape"], "dtypes": [], "pattern": "degenerate-shape-fastpath", "reduce_mode": "row-reduce", "structure": ["degenerate-shape", "vector-reduce", "tree-reduce"]}`

## 3. 正确性红线

- 退化条件判定过宽会遗漏输出段或混合不同归约域
- 树归约后段的非对齐地址及尾部全向量读取可能触发设备异常

资源与硬件约束：

- 每一级树归约的源/目标地址都必须满足向量 API 对齐要求，小于最小对齐跨度时改用安全收尾
- 尾 chunk 只能读取有效元素或有明确 guard 区，禁止依赖越界向量读取

## 4. 泛化条件

- 策略作用域：common（跨 operator class）

适用：

- host 能从 shape 和 axis 证明输出元素数很小，且被归约数据在当前视图中可连续或规则分段访问
- 归约算子存在可向量化的结合形式，并能为尾块提供合法 mask
- 累加器和中间树归约缓冲满足 UB、寄存器及对齐限制

不适用：

- 输出仍包含大量独立段、索引映射不规则或归约顺序具有强语义约束时应使用通用路径
- 目标 dtype 需要更高精度累加但片上资源无法容纳提升后的累加器时不适用

## 5. 实施步骤

1. 在 host 侧规范化 axis 并计算输出元素数，为可证明的退化形状设置独立 tiling key
2. 按向量宽度连续读取输入并累加到多个 lane，尾 chunk 使用精确 mask
3. 在 UB 或寄存器内分层折半归约，只有满足对齐的层级使用向量指令
4. 对最后少量 lane 使用受控的标量收尾或专用归约指令
5. 非退化 shape、非连续布局和不支持 dtype 回退到通用归约

## 6. LLM 前置问题

- 目标实现是否满足：host 能从 shape 和 axis 证明输出元素数很小，且被归约数据在当前视图中可连续或规则分段访问？
- 目标实现是否满足：归约算子存在可向量化的结合形式，并能为尾块提供合法 mask？
- 目标实现是否满足：累加器和中间树归约缓冲满足 UB、寄存器及对齐限制？
- 是否命中排除条件：输出仍包含大量独立段、索引映射不规则或归约顺序具有强语义约束时应使用通用路径？

## 7. 验收标准

正确性：

- 覆盖空输入、单元素、刚好一个向量、非整向量尾部、极大归约长度和不同 axis 组合
- 按算子契约验证 NaN、Inf、溢出及高精度累加行为

性能：

- 比较退化与非退化多组形状，确认标量循环、中间 GM 写回和通用索引开销消失且回退路径无回归

回滚信号：

- 出现 axis 误判、尾部越界、对齐异常、精度漂移或非退化路径误命中时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`common`
- Related anti-patterns：无

- strategy-unsorted-segment-sum-20260820-uss-005（status=accepted, case=15, speedup=3055.6）
- ksearch-arg-max-<run-id>（status=accepted, case=1, speedup=3.25）
- adaptive_avg_pool_3d-<run-id>（round=1, status=accepted）
- adaptive_avg_pool_3d-<run-id>（round=1, status=accepted）

## 检索卡（短卡）

动作：以连续向量累加和片上树归约绕过通用索引映射、分块及中间写回。
适用：host可证明输出很少、数据可连续或规则分段访问，且归约具有可向量化的结合形式。
限制：各级树归约地址须满足向量 API 对齐；退化判定不得混合归约域或遗漏输出段。
范围：跨算子类的退化形状全归约快路径。
检索词：128-lane累加器、尾chunk掩码、片上树归约、tiling key
机会：极少输出路径仍保留通用索引映射、分块和中间写回。
