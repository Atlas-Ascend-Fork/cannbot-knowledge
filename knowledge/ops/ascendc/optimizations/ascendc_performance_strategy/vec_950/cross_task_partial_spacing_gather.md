---
type: Optimization
title: 核间标量 partial 稀疏落盘与分块收集
description: 将不同核的小记录从紧凑相邻存储改为带间距的槽位，同时把最终读取改为跨步 DMA 收集。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/cross-task-partial-spacing-gather.md
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
      "稀疏空间及收集成本超过写回收益"
    ],
    "required_conditions": [
      "多核各写少量标量，最终阶段统一合并",
      "workspace、producer、consumer共享布局协议"
    ]
  },
  "classification": "performance_strategy",
  "created": "2026-10-16",
  "feature_signature": {
    "bottleneck": [
      "adjacent-small-global-stores",
      "scalar-final-collection"
    ],
    "pattern": "cross-task-partial-spacing-gather"
  },
  "generality": "pattern",
  "id": "cross-task-partial-spacing-gather",
  "implementation_steps": [
    "为各字段定义载荷字节数、间距和对齐，推导 workspace 总量及溢出界。",
    "统一生产和收集地址协议，候选间距与紧凑方案分别保留。",
    "用跨步 DataCopyPad 收集到显式填充的 UB 块，按有效槽位掩码合并。",
    "检查完整调用中写回、收集、归约的净成本，再决定门控。"
  ],
  "intent": "每核只写一个和与一个计数，核数增加后小记录写回不成比例变慢；最终合并仍逐标量取数。",
  "mechanism": "将不同核的小记录分开放置，再以跨步DMA和显式padding组织向量归约。",
  "name": "核间标量 partial 稀疏落盘与分块收集",
  "operator_scope": "分阶段归约的每核输出仅为少量标量，且后续消费者可批量收集；总槽位大小及最终 UB 布局均可预算。浮点合并顺序允许按原容差验证。",
  "phase": [
    "design",
    "tuning"
  ],
  "principle": "多核同时向 GM 写入很小的相邻记录时，紧凑布局未必具有最优写回效率。让每核拥有独立间距槽位，可以改变并发小写入的交互；最终用 DataCopyPad 将有效载荷收集到 UB，并将每项补成向量可加载的块。该方法同时改变写回和收集布局，不能仅凭收益推断具体缓存争用原因。128B 可作为候选间距，不能直接当作已知缓存行大小。",
  "provenance": {
    "source_report": "AOA_skill PR#15 commit c7d842a"
  },
  "risks": [
    "主机分配、生产者地址计算和消费者跨步必须使用同一协议及门控，不能只改一端",
    "空核也须写中性元；padding 和尾部槽位必须显式置为中性元，不能让旧 NaN 参与归约",
    "DMA 长度、GM stride 按字节计算，UB padding 按元素计算",
    "计数窄化或提取低字前必须证明总数上界及高字为零；否则保留完整宽度",
    "生产完成后才能收集"
  ],
  "schema_version": 2,
  "slug": "cross-task-partial-spacing-gather",
  "source": "aoa_skill_pr15",
  "status": "pending",
  "summary": "将不同核的小记录从紧凑相邻存储改为带间距的槽位，同时把最终读取改为跨步 DMA 收集。",
  "verification": {
    "correctness": [
      "覆盖单核、核数边界、空核及不整向量尾部，核对计数和特殊值"
    ],
    "performance": [
      "比较完整调用与生产、合并各阶段耗时；仅在净收益成立的范围启用，不能把写回改善抵消在 final 阶段"
    ],
    "rollback_signals": [
      "每核已连续写出大块数据，或核数使稀疏空间、DMA 描述符和 padding 开销过大",
      "保留紧凑布局回退，不套用固定核数上限"
    ]
  }
}
-->

# 性能优化策略：核间标量 partial 稀疏落盘与分块收集

单一优化点：将不同核的小记录从紧凑相邻存储改为带间距的槽位，同时把最终读取改为跨步 DMA 收集。

## 1. 原理

多核同时向 GM 写入很小的相邻记录时，紧凑布局未必具有最优写回效率。让每核拥有独立间距槽位，可以改变并发小写入的交互；最终用 DataCopyPad 将有效载荷收集到 UB，并将每项补成向量可加载的块。该方法同时改变写回和收集布局，不能仅凭收益推断具体缓存争用原因。128B 可作为候选间距，不能直接当作已知缓存行大小。

## 2. 性能问题模式

每核只写一个和与一个计数，核数增加后小记录写回不成比例变慢；最终合并仍逐标量取数。目标是改善核间小写入及最终收集，不是扩大每核累加状态。代价是额外 GM 空间、跨步读取、UB padding 和可能改变的归约顺序。

## 3. 正确性红线

主机分配、生产者地址计算和消费者跨步必须使用同一协议及门控，不能只改一端。空核也须写中性元；padding 和尾部槽位必须显式置为中性元，不能让旧 NaN 参与归约。DMA 长度、GM stride 按字节计算，UB padding 按元素计算。计数窄化或提取低字前必须证明总数上界及高字为零；否则保留完整宽度。生产完成后才能收集。

## 4. 泛化条件

适用：分阶段归约的每核输出仅为少量标量，且后续消费者可批量收集；总槽位大小及最终 UB 布局均可预算。浮点合并顺序允许按原容差验证。

不适用或需退回：每核已连续写出大块数据，或核数使稀疏空间、DMA 描述符和 padding 开销过大。保留紧凑布局回退，不套用固定核数上限。

## 5. 实施步骤

1. 为各字段定义载荷字节数、间距和对齐，推导 workspace 总量及溢出界。
2. 统一生产和收集地址协议，候选间距与紧凑方案分别保留。
3. 用跨步 DataCopyPad 收集到显式填充的 UB 块，按有效槽位掩码合并。
4. 检查完整调用中写回、收集、归约的净成本，再决定门控。

## 6. LLM 前置问题

相邻小写入是否构成开销？每个字段的宽度和计数上界是什么？间距增加后的 workspace 是否可接受？最后一组和空核如何初始化？

## 7. 验收标准

覆盖单核、核数边界、空核及不整向量尾部，核对计数和特殊值。比较完整调用与生产、合并各阶段耗时；仅在净收益成立的范围启用，不能把写回改善抵消在 final 阶段。

## 8. 分类与证据

- Classification：`performance_strategy`
- Generality：`pattern`
- Related anti-patterns：无

- 尚无归档证据（provenance：AOA_skill PR#15 commit c7d842a）。

## 检索卡（短卡）

动作：将各核小partial分隔落盘，再用跨步DMA收集到显式padding的UB块做向量合并。
适用：每核仅输出少量标量；分配、生产、消费共用布局；workspace及UB预算成立。
限制：空核及padding写中性元；字节stride与元素padding分清；计数窄化须证明上界；生产后消费。
范围：分阶段多核标量归约的写回与最终收集。
检索词：partial spacing、DataCopyPad、GM stride、UB padding、SIMD
机会：相邻核小记录写回扩展性差，最终阶段仍逐标量取数。
代价：稀疏workspace、跨步读取及UB填充；合并次序可能变化。
