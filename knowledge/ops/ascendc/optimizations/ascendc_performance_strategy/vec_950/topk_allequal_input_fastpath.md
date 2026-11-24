---
type: Optimization
title: all-equal/monotone 输入检测的 top-k 直接发射快路径
description: kernel-side self-select：对 sortLen 内做向量化 MAX/MIN 归约检测行内是否全等（all-equal / monotone），若全等则直接按 largest 方向发射 y=value、idx=0..k-1；否则逐字节回退 ComputeTopK。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/topk-allequal-input-fastpath.md
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
      "全等检测必须精确覆盖 sortLen 个元素，禁止越界向量读取",
      "回退路径必须与 baseline ComputeTopK 逐字节一致",
      "收益依赖数据条件（100% all-zero 对固定 eval 确定）"
    ],
    "excluded_conditions": [
      "非全等输入（全等检测失败率高的分布下检测开销成纯负担）",
      "全 NaN 语义与 golden 不一致的 dtype",
      "数据分布不确定时须保留完整回退"
    ],
    "required_conditions": [
      "输入数据生成可确定/可预期为整行常数值（如 value_range=[0,0] 的 all-zero）",
      "sortLen 在向量归约可一次覆盖的范围内（本 run 1013）",
      "存在向量化 MAX/MIN 归约且可精确 mask 尾块"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "8db7f687ba9f7c2de1e0b0218abe7e32625602636509b1c8c5923c71206dff2d",
      "decision_sha256": "bb0e623972b2ef33d93c7bedfeb9106f4a9fa3fd4353766aba61a132b55287ac",
      "operator_class": "sort-select",
      "performance_sha256": "7b3dcc6a53cca7c8fe3a6bbaa991410b6d89c1c2ba221b1496bec3b47f12a4c8",
      "round": 3,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "c85ae0a1c31162ec77027e1a8f0b49ae4a6cb73872e5d2457cd6f1cf6967381c",
      "verify_sha256": "86ad1241aa3eb53915a47dc846fec1a6f2407b7410bb797d913efec1de903321"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-serial",
      "all-equal-input"
    ],
    "dtypes": [
      "int64"
    ],
    "pattern": "allequal-input-fastpath",
    "reduce_mode": "top-k",
    "structure": [
      "vector-maxmin-reduce",
      "direct-emit",
      "t1-es1-whole-row"
    ]
  },
  "generality": "op_class",
  "id": "TOPK-ALLEQUAL-INPUT-FASTPATH",
  "implementation_steps": [
    "确认目标 case 数据分布（cases.yaml value_range）为常数值",
    "实现向量化 MAX/MIN 归约精确检测 sortLen 内全等",
    "全等时按 largest 语义直接发射 y/idx（k 份），否则回退",
    "verify 全量 + 官方路径 spot_check 复现"
  ],
  "intent": "消除全等输入上无信息量的标量有界堆比较（3M 次堆比较全是 tie）：case_16 baseline aiv_scalar 0.996、~637us 标量 / 全算子 639us。",
  "mechanism": "Init 中解码 sortLen/k/largest/dtype 后自选 all-equal 快路径：向量化 MAX/MIN reduce 精确覆盖 sortLen_ 个元素，比较 max==min（注意全 NaN 语义），全等则直接按 k 发射 value/idx；非全等或 dtype/边界不满足时逐字节走 ComputeTopK 回退。",
  "name": "all-equal/monotone 输入检测的 top-k 直接发射快路径",
  "operator_class": "sort-select",
  "operator_scope": "top_k 中输入整行为常数值（如 100% all-zero 数据生成）的 case：检测到全等行后 top-k 退化为 k 份同值 + 索引 0..k-1，可绕过完整排序/堆。",
  "principle": "当整行元素全等时，top-k 结果与排序无关且可解析确定（k 份同值，索引按语义 0..k-1）；用一次向量化 MAX/MIN 归约即可判定该退化条件，判定成本 O(N) 向量指令远低于堆的 O(N log k) 标量比较。",
  "related_anti_patterns": [
    "scalar-bounded-heap-fill-finalize"
  ],
  "risks": [
    "检测条件过宽把非全等行误判为全等（正确性风险）",
    "全 NaN 等边界的 golden 语义不一致",
    "收益是数据条件相关的（非全等输入下检测开销纯负担）"
  ],
  "slug": "topk-allequal-input-fastpath",
  "summary": "kernel-side self-select：对 sortLen 内做向量化 MAX/MIN 归约检测行内是否全等（all-equal / monotone），若全等则直接按 largest 方向发射 y=value、idx=0..k-1；否则逐字节回退 ComputeTopK。参考主线上游 AICPU DetectMonotone/EmitMonotoneTopK 模式。",
  "verification": {
    "correctness": [
      "verify 10/10 通过；非全等逐字节回退 ComputeTopK",
      "case_16 官方路径 spot_check 181.6us 可复现（measure 149.3us）"
    ],
    "performance": [
      "case_16 639.5us -> 149.3us（measure）≈4.28x / 181.6us（official-path）≈3.6x",
      "score_model 边际 +0.81 官方 pts（estimate）"
    ],
    "rollback_signals": [
      "任何非全等 case 被误路由/回退路径回归则回退",
      "spot_check verdict=not_reproducible 时回退"
    ]
  }
}
-->

# 性能优化策略：all-equal/monotone 输入检测的 top-k 直接发射快路径

单一优化点：kernel-side self-select：对 sortLen 内做向量化 MAX/MIN 归约检测行内是否全等（all-equal / monotone），若全等则直接按 largest 方向发射 y=value、idx=0..k-1；否则逐字节回退 ComputeTopK。参考主线上游 AICPU DetectMonotone/EmitMonotoneTopK 模式。

## 1. 原理

当整行元素全等时，top-k 结果与排序无关且可解析确定（k 份同值，索引按语义 0..k-1）；用一次向量化 MAX/MIN 归约即可判定该退化条件，判定成本 O(N) 向量指令远低于堆的 O(N log k) 标量比较。

实现机制：Init 中解码 sortLen/k/largest/dtype 后自选 all-equal 快路径：向量化 MAX/MIN reduce 精确覆盖 sortLen_ 个元素，比较 max==min（注意全 NaN 语义），全等则直接按 k 发射 value/idx；非全等或 dtype/边界不满足时逐字节走 ComputeTopK 回退。

## 2. 性能问题模式

- 优化目标：消除全等输入上无信息量的标量有界堆比较（3M 次堆比较全是 tie）：case_16 baseline aiv_scalar 0.996、~637us 标量 / 全算子 639us。
- 适用数据流：top_k 中输入整行为常数值（如 100% all-zero 数据生成）的 case：检测到全等行后 top-k 退化为 k 份同值 + 索引 0..k-1，可绕过完整排序/堆。
- Feature signature：`{"bottleneck": ["scalar-serial", "all-equal-input"], "dtypes": ["int64"], "pattern": "allequal-input-fastpath", "reduce_mode": "top-k", "structure": ["vector-maxmin-reduce", "direct-emit", "t1-es1-whole-row"]}`

## 3. 正确性红线

- 检测条件过宽把非全等行误判为全等（正确性风险）
- 全 NaN 等边界的 golden 语义不一致
- 收益是数据条件相关的（非全等输入下检测开销纯负担）

资源与硬件约束：

- 全等检测必须精确覆盖 sortLen 个元素，禁止越界向量读取
- 回退路径必须与 baseline ComputeTopK 逐字节一致
- 收益依赖数据条件（100% all-zero 对固定 eval 确定）

## 4. 泛化条件

- 策略作用域：op_class：sort-select

适用：

- 输入数据生成可确定/可预期为整行常数值（如 value_range=[0,0] 的 all-zero）
- sortLen 在向量归约可一次覆盖的范围内（本 run 1013）
- 存在向量化 MAX/MIN 归约且可精确 mask 尾块

不适用：

- 非全等输入（全等检测失败率高的分布下检测开销成纯负担）
- 全 NaN 语义与 golden 不一致的 dtype
- 数据分布不确定时须保留完整回退

## 5. 实施步骤

1. 确认目标 case 数据分布（cases.yaml value_range）为常数值
2. 实现向量化 MAX/MIN 归约精确检测 sortLen 内全等
3. 全等时按 largest 语义直接发射 y/idx（k 份），否则回退
4. verify 全量 + 官方路径 spot_check 复现

## 6. LLM 前置问题

- 目标实现是否满足：输入数据生成可确定/可预期为整行常数值（如 value_range=[0,0] 的 all-zero）？
- 目标实现是否满足：sortLen 在向量归约可一次覆盖的范围内（本 run 1013）？
- 目标实现是否满足：存在向量化 MAX/MIN 归约且可精确 mask 尾块？
- 是否命中排除条件：非全等输入（全等检测失败率高的分布下检测开销成纯负担）？

## 7. 验收标准

正确性：

- verify 10/10 通过；非全等逐字节回退 ComputeTopK
- case_16 官方路径 spot_check 181.6us 可复现（measure 149.3us）

性能：

- case_16 639.5us -> 149.3us（measure）≈4.28x / 181.6us（official-path）≈3.6x
- score_model 边际 +0.81 官方 pts（estimate）

回滚信号：

- 任何非全等 case 被误路由/回退路径回归则回退
- spot_check verdict=not_reproducible 时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：scalar-bounded-heap-fill-finalize

- top_k-20260831_151225-dbf26e（round=3, status=accepted）

## 检索卡（短卡）

动作：对 sortLen 内做向量化 MAX/MIN 归约检测整行是否全等，全等则直接发射 y=value、idx=0..k-1。
适用：输入数据生成可预期为整行常数值（如 value_range=[0,0]）；sortLen 在向量归约一次可覆盖范围内。
限制：全等检测须精确覆盖 sortLen 个元素，禁越界读取；非全等须逐字节回退 ComputeTopK。
范围：top_k 中整行为常数值的 T1/ES1 整行 case
检索词：向量化 MAX/MIN 归约、all-equal 检测、largest 语义、ComputeTopK 回退、scalar-bounded-heap
机会：全等输入上堆比较全是 tie，aiv_scalar 0.996 占全算子 639us 中约 637us
代价：收益依赖数据条件，非全等分布下检测开销纯负担
