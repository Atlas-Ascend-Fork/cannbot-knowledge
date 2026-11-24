---
type: Optimization
title: 成对关系遍历融合排名与集体位掩码生成
description: 在已有成对遍历内顺带计排名，并用 warp ballot 并行压缩关系谓词。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/pair-pass-rank-ballot-fusion.md
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
      "仅为排名而新增平方级关系遍历",
      "非有限值未定义全序"
    ],
    "required_conditions": [
      "原算法已需遍历全部元素对",
      "优先级比较与确定性同分规则构成全序",
      "平台支持集体投票与归约"
    ]
  },
  "classification": "performance_strategy",
  "created": "2026-10-16",
  "feature_signature": {
    "bottleneck": [
      "separate-ranking-stage",
      "serial-predicate-packing"
    ],
    "pattern": "pair-pass-rank-ballot-fusion",
    "structure": [
      "pairwise-relation",
      "total-order-rank",
      "warp-ballot"
    ]
  },
  "generality": "pattern",
  "id": "PAIR-PASS-RANK-BALLOT-FUSION",
  "implementation_steps": [
    "定义统一全序比较器，证明同分与尾部规则下排名唯一。",
    "让 warp 各 lane 负责不同列，计算关系谓词并 ballot 写掩码字。",
    "同一遍累计优先级领先计数，经 warp 和块级归约写入顺序表。",
    "删除独立排序与冗余中间表示，保留生产消费依赖并核算完整调用成本。"
  ],
  "intent": "成对关系遍历与排序分别读取优先级，排序阶段并行度低；每个线程又串行计算整个掩码字，或先物化浮点关系矩阵再转掩码。",
  "mechanism": "在既有成对关系遍历中累计全序排名，以warp ballot直接生成位掩码，消除独立排序与逐位串行打包。",
  "name": "成对关系遍历融合排名与集体位掩码生成",
  "operator_scope": "原算法已需全部元素对的关系判断，排名依据与关系数据可同时获取，且平台支持 asc_ballot、asc_reduce_add 等集体操作。",
  "phase": [
    "design",
    "tuning"
  ],
  "principle": "若算法已经遍历所有元素对以生成关系掩码，可同时比较优先级，令每行累计排在自身之前的元素数。优先级与确定性同分规则构成全序时，该计数就是唯一排名，可直接写入顺序表，省去独立排序阶段。将一个掩码字的列分给 warp 各 lane，用 asc_ballot 汇集布尔谓词，可消除单线程逐列计算和移位拼接。",
  "provenance": {
    "source_report": "AOA_skill PR#15 commit c7d842a"
  },
  "risks": [
    "同分必须用稳定且唯一的原始索引等规则破平，保证排名互异、范围为有效元素区间，顺序表每槽恰写一次",
    "浮点非有限值必须另行定义全序；不能假定普通比较自动覆盖",
    "所有参与 lane 都必须执行集体操作，无效尾列贡献 false 和零计数；仅指定 lane 写掩码字，位序须与消费者一致",
    "跨 warp 累计及顺序表消费前必须完成同步"
  ],
  "schema_version": 2,
  "slug": "pair-pass-rank-ballot-fusion",
  "source": "aoa_skill_pr15",
  "status": "pending",
  "summary": "在已有成对遍历内顺带计排名，并用 warp ballot 并行压缩关系谓词。",
  "verification": {
    "correctness": [
      "核对全相同优先级、顺逆序、尾字及边界长度，排名必须构成置换且掩码逐位符合关系定义",
      "确认独立排序与冗余矩阵已删除，完整调用改善且新增比较和同步未成为主瓶颈"
    ],
    "performance": [
      "排名冲突、尾列污染、容量超限或整体回退时恢复分离路径"
    ],
    "rollback_signals": [
      "仅为了排名新增平方级遍历，或已有更低复杂度关系生成且不能复用",
      "融合仍增加平方级比较、优先级装载、归约和同步；关系矩阵大时掩码容量也是约束，不能因删除排序就推定整体获益"
    ]
  }
}
-->

# 性能优化策略：成对关系遍历融合排名与集体位掩码生成

单一优化点：在已有成对遍历内顺带计排名，并用 warp ballot 并行压缩关系谓词。

## 1. 原理

若算法已经遍历所有元素对以生成关系掩码，可同时比较优先级，令每行累计排在自身之前的元素数。优先级与确定性同分规则构成全序时，该计数就是唯一排名，可直接写入顺序表，省去独立排序阶段。将一个掩码字的列分给 warp 各 lane，用 asc_ballot 汇集布尔谓词，可消除单线程逐列计算和移位拼接。

## 2. 性能问题模式

成对关系遍历与排序分别读取优先级，排序阶段并行度低；每个线程又串行计算整个掩码字，或先物化浮点关系矩阵再转掩码。融合复用已读取的元素对，只增加优先级比较与计数归约，并直接产出紧凑位掩码。

## 3. 正确性红线

同分必须用稳定且唯一的原始索引等规则破平，保证排名互异、范围为有效元素区间，顺序表每槽恰写一次。浮点非有限值必须另行定义全序；不能假定普通比较自动覆盖。所有参与 lane 都必须执行集体操作，无效尾列贡献 false 和零计数；仅指定 lane 写掩码字，位序须与消费者一致。跨 warp 累计及顺序表消费前必须完成同步。

## 4. 泛化条件

适用：原算法已需全部元素对的关系判断，排名依据与关系数据可同时获取，且平台支持 asc_ballot、asc_reduce_add 等集体操作。

不适用：仅为了排名新增平方级遍历，或已有更低复杂度关系生成且不能复用。融合仍增加平方级比较、优先级装载、归约和同步；关系矩阵大时掩码容量也是约束，不能因删除排序就推定整体获益。

## 5. 实施步骤

1. 定义统一全序比较器，证明同分与尾部规则下排名唯一。
2. 让 warp 各 lane 负责不同列，计算关系谓词并 ballot 写掩码字。
3. 同一遍累计优先级领先计数，经 warp 和块级归约写入顺序表。
4. 删除独立排序与冗余中间表示，保留生产消费依赖并核算完整调用成本。

## 6. LLM 前置问题

- 成对遍历是原本必要工作，还是融合后新增的复杂度？
- 同分和非有限值能否产生唯一、完整的排名？
- ballot 参与掩码、尾列、字位序及跨 warp 同步是否完整？

## 7. 验收标准

核对全相同优先级、顺逆序、尾字及边界长度，排名必须构成置换且掩码逐位符合关系定义。确认独立排序与冗余矩阵已删除，完整调用改善且新增比较和同步未成为主瓶颈。排名冲突、尾列污染、容量超限或整体回退时恢复分离路径。

## 8. 分类与证据

- Classification：`performance_strategy`
- Generality：`pattern`
- Related anti-patterns：无

- 尚无归档证据（provenance：AOA_skill PR#15 commit c7d842a）。

## 检索卡（短卡）

动作：在既有成对关系遍历内累计唯一排名，并用warp ballot并行压缩关系谓词。
适用：原算法已需全部元素对判断，排名与关系数据可同时获取，平台支持集体投票和归约。
限制：同分须破平保证排名唯一；非有限值另定全序；所有lane参与，尾列为false，消费前同步。
范围：成对关系筛选的排名与位掩码生成。
检索词：asc_ballot、asc_reduce_add、warp、全序排名、位掩码、同分破平
机会：成对遍历与低并行排序重复读优先级，单线程串行拼掩码或物化浮点关系矩阵。
代价：增加平方级优先级比较、装载、归约和同步，掩码容量仍受约束。
