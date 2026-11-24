---
type: Optimization
title: TopK 的 UB 常驻有界二叉堆
description: 用容量 k 的 UB 二叉堆将 TopK 候选替换降为 O(log k)，并以堆排完成输出。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/bounded-heap-candidate-selection.md
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
      "堆比较器必须把值、索引、方向和特殊值规则组合成严格一致的顺序",
      "candVal/candIdx 堆及排序临时量必须满足 UB 容量和地址对齐"
    ],
    "excluded_conditions": [
      "k 极小且输入很短时简单线性候选路径可能更快，应按实测设置切换阈值",
      "候选集合无法常驻 UB，或要求的全局稳定排序不能由堆比较器保证时不适用"
    ],
    "required_conditions": [
      "需要从较长轴选择 k 个候选，且线性替换扫描或二次 finalize 已成为热点",
      "k 个值和索引可以常驻 UB",
      "比较语义可实现为保持最差候选在根节点的有界堆"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-08-23",
  "evidence": [
    {
      "after_us": 1159780.023,
      "before_us": 94569004.917,
      "case": "20-case-sum",
      "operator_class": "sort-select",
      "precision": "20/20 PASS, repeated 3x",
      "run_id": "<run-id>",
      "source_report": "<PERF_ROOT>/strategies/top_k_opt_20260820.md",
      "speedup": 81.54,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "candidate-linear-scan",
      "quadratic-finalize"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "bounded-heap-top-k",
    "reduce_mode": "top-k",
    "structure": [
      "binary-heap",
      "ub-resident",
      "heap-sort"
    ]
  },
  "gain": "20 用例耗时和 94,569,004.917→1,159,780.023us，总体 81.54x；逐例 1.76–155.13x，3 次重复稳定。",
  "generality": "op_class",
  "id": "TOPK-BOUNDED-HEAP",
  "implementation_steps": [
    "定义统一比较器，使堆根始终是当前候选中最应淘汰的值索引对",
    "填充阶段追加候选并 sift-up，达到 k 后固定为容量 k 的堆",
    "对新输入先与根 O(1) 比较，命中替换时写根并执行 O(log k) sift-down",
    "输入结束后在片上执行堆排序或等价 O(k log k) finalize，按输出契约生成有序结果",
    "为小 k/短轴保留简单路径，并验证所有 flag 位随值索引对整体移动"
  ],
  "intent": "把 TopK 稳态候选维护和最终排序从线性/二次复杂度降为对数复杂度。",
  "mechanism": "在 UB 的 candVal/candIdx 上维护容量为 k 的二叉堆，根为最差候选；填充使用 sift-up，稳态仅在新值胜过根时替换并 sift-down，最后用堆排序输出。",
  "name": "TopK 的 UB 常驻有界二叉堆",
  "op": "top_k",
  "operator_class": "sort-select",
  "operator_scope": "轴长和 k 较大、候选维护与 finalize 复杂度主导的流式 TopK 选择排序",
  "principle": "线性扫描维护 k 个候选会产生 O(Nk)，插入式 finalize 还可能达到 O(k²)；有界堆让阈值查询为 O(1)、替换和最终排序为 O(log k)/O(k log k)。",
  "provenance": {
    "final_summary": "<PERF_ROOT>/strategies/top_k_opt_20260820/final_summary.json",
    "source_report": "<PERF_ROOT>/strategies/top_k_opt_20260820.md"
  },
  "related_anti_patterns": [],
  "risks": [
    "值与索引没有成对移动会破坏并列规则或输出对应关系",
    "错误的 largest/smallest 比较方向会让堆根语义反转并产生全局错误"
  ],
  "schema_version": 2,
  "slug": "bounded-heap-candidate-selection",
  "source": "external_verified",
  "status": "applied",
  "summary": "用容量 k 的 UB 二叉堆将 TopK 候选替换降为 O(log k)，并以堆排完成输出。",
  "verification": {
    "correctness": [
      "覆盖 k 边界、largest/smallest、sorted 开关、重复值、NaN、不同 index dtype，并与参考实现逐项核对"
    ],
    "performance": [
      "跨轴长与 k 网格比较简单路径、缓存最差路径和堆路径，确认选择阈值与复杂度趋势"
    ],
    "rollback_signals": [
      "堆不变量破坏、值索引错配、特殊值语义错误或小 k 路径稳定回归时回退"
    ]
  }
}
-->

# 性能优化策略：TopK 的 UB 常驻有界二叉堆

单一优化点：用容量 k 的 UB 二叉堆将 TopK 候选替换降为 O(log k)，并以堆排完成输出。

## 1. 原理

线性扫描维护 k 个候选会产生 O(Nk)，插入式 finalize 还可能达到 O(k²)；有界堆让阈值查询为 O(1)、替换和最终排序为 O(log k)/O(k log k)。

实现机制：在 UB 的 candVal/candIdx 上维护容量为 k 的二叉堆，根为最差候选；填充使用 sift-up，稳态仅在新值胜过根时替换并 sift-down，最后用堆排序输出。

## 2. 性能问题模式

- 优化目标：把 TopK 稳态候选维护和最终排序从线性/二次复杂度降为对数复杂度。
- 适用数据流：轴长和 k 较大、候选维护与 finalize 复杂度主导的流式 TopK 选择排序
- Feature signature：`{"bottleneck": ["candidate-linear-scan", "quadratic-finalize"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "bounded-heap-top-k", "reduce_mode": "top-k", "structure": ["binary-heap", "ub-resident", "heap-sort"]}`

## 3. 正确性红线

- 值与索引没有成对移动会破坏并列规则或输出对应关系
- 错误的 largest/smallest 比较方向会让堆根语义反转并产生全局错误

资源与硬件约束：

- 堆比较器必须把值、索引、方向和特殊值规则组合成严格一致的顺序
- candVal/candIdx 堆及排序临时量必须满足 UB 容量和地址对齐

## 4. 泛化条件

- 策略作用域：op_class：sort-select

适用：

- 需要从较长轴选择 k 个候选，且线性替换扫描或二次 finalize 已成为热点
- k 个值和索引可以常驻 UB
- 比较语义可实现为保持最差候选在根节点的有界堆

不适用：

- k 极小且输入很短时简单线性候选路径可能更快，应按实测设置切换阈值
- 候选集合无法常驻 UB，或要求的全局稳定排序不能由堆比较器保证时不适用

## 5. 实施步骤

1. 定义统一比较器，使堆根始终是当前候选中最应淘汰的值索引对
2. 填充阶段追加候选并 sift-up，达到 k 后固定为容量 k 的堆
3. 对新输入先与根 O(1) 比较，命中替换时写根并执行 O(log k) sift-down
4. 输入结束后在片上执行堆排序或等价 O(k log k) finalize，按输出契约生成有序结果
5. 为小 k/短轴保留简单路径，并验证所有 flag 位随值索引对整体移动

## 6. LLM 前置问题

- 目标实现是否满足：需要从较长轴选择 k 个候选，且线性替换扫描或二次 finalize 已成为热点？
- 目标实现是否满足：k 个值和索引可以常驻 UB？
- 目标实现是否满足：比较语义可实现为保持最差候选在根节点的有界堆？
- 是否命中排除条件：k 极小且输入很短时简单线性候选路径可能更快，应按实测设置切换阈值？

## 7. 验收标准

正确性：

- 覆盖 k 边界、largest/smallest、sorted 开关、重复值、NaN、不同 index dtype，并与参考实现逐项核对

性能：

- 跨轴长与 k 网格比较简单路径、缓存最差路径和堆路径，确认选择阈值与复杂度趋势

回滚信号：

- 堆不变量破坏、值索引错配、特殊值语义错误或小 k 路径稳定回归时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- strategy-top-k-20260820-topk-002（status=accepted, case=20-case-sum, speedup=81.54）

## 检索卡（短卡）

动作：将TopK候选的线性维护和插入式finalize改为UB常驻容量k的有界二叉堆。
适用：较长轴选择k个候选，线性替换或二次finalize成为热点，且值和索引可常驻UB。
限制：比较器须统一编码值、索引、方向和特殊值顺序；堆操作必须成对移动值与索引。
范围：selection-sort/top-k的流式候选维护与最终排序。
检索词：TopK、有界二叉堆、candVal、candIdx、sift-up、淘汰阈值
机会：候选维护为O(Nk)线性扫描，插入式finalize可达O(k²)。
