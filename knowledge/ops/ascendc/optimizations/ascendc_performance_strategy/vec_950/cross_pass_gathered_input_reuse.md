---
type: Optimization
title: 跨 pass 复用已 Gather 的原输入
description: 将第一遍 Gather 得到的原输入按消费布局暂存，第二遍改用对齐加载，删除重复索引重排。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/cross-pass-gathered-input-reuse.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "excluded_conditions": [
      "对齐行已有更便宜批搬路径",
      "两次Gather的输入或索引不同"
    ],
    "required_conditions": [
      "既有短行Gather路径反复重排同一原输入",
      "FP32连续归约轴，3≤R≤128且R%8!=0",
      "UB容量及跨pass屏障成立"
    ]
  },
  "classification": "performance_strategy",
  "created": "2026-10-16",
  "feature_signature": {
    "bottleneck": [
      "duplicate-indexed-gather",
      "short-row-reorder"
    ],
    "pattern": "cross-pass-gathered-input-reuse"
  },
  "generality": "pattern",
  "id": "cross-pass-gathered-input-reuse",
  "implementation_steps": [
    "对齐两遍 Gather 的索引表达式，确认完全同源。",
    "首遍在原统计后 StoreAlign 原输入到下一遍易加载的布局。",
    "添加必要 LocalMemBar，次遍 LoadAlign，读后覆写为变换结果。",
    "保留对齐与通用路径，仅在明确门控分支启用。"
  ],
  "intent": "连续短行因行长非对齐而采用 Gather，统计和变换两遍重复执行索引读取；向量重排比普通加载昂贵。",
  "mechanism": "首次Gather后将重排原输入暂存UB，下一pass对齐加载并覆写同一scratch。",
  "name": "跨 pass 复用已 Gather 的原输入",
  "operator_scope": "既有 FP32 连续归约轴短行 Gather 路径，3≤R≤128、R%8!=0，所需 UB 布局可容纳，并且省下的重复 Gather 超过暂存成本。",
  "phase": [
    "design",
    "tuning"
  ],
  "principle": "短行的多遍归约可将多行相同列 Gather 到 SIMD lane，以利于跨行并行。若统计遍与后续变换遍对同一 UB 输入执行相同 Gather，第一遍可在统计后把重排后的原输入写入 scratch；建立本地写读屏障后，下一遍 LoadAlign 直接消费，并在原输入最后一次使用后把该槽覆写为变换结果。复用对象是重排后的原输入，不是指数等变换结果；本机制不减少 GM 读写。",
  "provenance": {
    "source_report": "AOA_skill PR#15 commit c7d842a"
  },
  "risks": [
    "两遍输入、索引及类型必须相同，第一遍不能改变原值位型；若第二遍依赖新的索引或已更新数据则不适用",
    "scratch 必须有独立生命周期及容量证明，只有读完原输入后才能就地覆写",
    "VEC_STORE 到 VEC_LOAD 的可见性、有效 lane 及尾掩码须完整；未写 lane 不能以旧 NaN 污染统计",
    "保持原特殊值处理、变换顺序和最终舍入"
  ],
  "schema_version": 2,
  "slug": "cross-pass-gathered-input-reuse",
  "source": "aoa_skill_pr15",
  "status": "pending",
  "summary": "将第一遍 Gather 得到的原输入按消费布局暂存，第二遍改用对齐加载，删除重复索引重排。",
  "verification": {
    "correctness": [
      "覆盖门控两侧、临近行长、非满行组及特殊值；核对编译资源和输出语义"
    ],
    "performance": [
      "比较完整调用并检查对齐回退路径，若新增 UB 访问及屏障抵消收益则缩小门控或退回"
    ],
    "rollback_signals": [
      "对齐行 R%8==0 保留 NDDMA 或原批搬路径；其他类型、轴布局或更长行必须重新建立预算和性能门控",
      "不能因少数非对齐长度有收益推广全部短行"
    ]
  }
}
-->

# 性能优化策略：跨 pass 复用已 Gather 的原输入

单一优化点：将第一遍 Gather 得到的原输入按消费布局暂存，第二遍改用对齐加载，删除重复索引重排。

## 1. 原理

短行的多遍归约可将多行相同列 Gather 到 SIMD lane，以利于跨行并行。若统计遍与后续变换遍对同一 UB 输入执行相同 Gather，第一遍可在统计后把重排后的原输入写入 scratch；建立本地写读屏障后，下一遍 LoadAlign 直接消费，并在原输入最后一次使用后把该槽覆写为变换结果。复用对象是重排后的原输入，不是指数等变换结果；本机制不减少 GM 读写。

## 2. 性能问题模式

连续短行因行长非对齐而采用 Gather，统计和变换两遍重复执行索引读取；向量重排比普通加载昂贵。代价是 UB store、LoadAlign、LocalMemBar 和延长 scratch 生命周期。对齐行若已有 NDDMA 或批量转置，额外暂存可能比原路径更慢。

## 3. 正确性红线

两遍输入、索引及类型必须相同，第一遍不能改变原值位型；若第二遍依赖新的索引或已更新数据则不适用。scratch 必须有独立生命周期及容量证明，只有读完原输入后才能就地覆写。VEC_STORE 到 VEC_LOAD 的可见性、有效 lane 及尾掩码须完整；未写 lane 不能以旧 NaN 污染统计。保持原特殊值处理、变换顺序和最终舍入。

## 4. 泛化条件

适用：既有 FP32 连续归约轴短行 Gather 路径，3≤R≤128、R%8!=0，所需 UB 布局可容纳，并且省下的重复 Gather 超过暂存成本。

不适用或需退回：对齐行 R%8==0 保留 NDDMA 或原批搬路径；其他类型、轴布局或更长行必须重新建立预算和性能门控。不能因少数非对齐长度有收益推广全部短行。

## 5. 实施步骤

1. 对齐两遍 Gather 的索引表达式，确认完全同源。
2. 首遍在原统计后 StoreAlign 原输入到下一遍易加载的布局。
3. 添加必要 LocalMemBar，次遍 LoadAlign，读后覆写为变换结果。
4. 保留对齐与通用路径，仅在明确门控分支启用。

## 6. LLM 前置问题

重复成本来自 Gather 还是变换重算？scratch 是否原已存在？UB 总量及尾行如何计算？对齐行是否已有更便宜路径？屏障是否与访问顺序匹配？

## 7. 验收标准

覆盖门控两侧、临近行长、非满行组及特殊值；核对编译资源和输出语义。比较完整调用并检查对齐回退路径，若新增 UB 访问及屏障抵消收益则缩小门控或退回。

## 8. 分类与证据

- Classification：`performance_strategy`
- Generality：`pattern`
- Related anti-patterns：无

- 尚无归档证据（provenance：AOA_skill PR#15 commit c7d842a）。

## 检索卡（短卡）

动作：首遍Gather后把重排原输入暂存UB，次遍对齐加载并在读后覆写scratch。
适用：既有FP32连续轴短行Gather路径；3≤R≤128且R%8!=0；UB预算成立。
限制：输入和索引同源；先屏障再读、最后使用后覆写；保持尾掩码；R%8==0保留原路径。
范围：非对齐短行多pass归约的输入重排。
检索词：Gather、LoadAlign、StoreAlign、LocalMemBar、UB scratch
机会：统计与变换两遍对同一输入重复做索引Gather。
代价：新增UB写读与屏障；GM流量不减；对齐行可能更慢。
