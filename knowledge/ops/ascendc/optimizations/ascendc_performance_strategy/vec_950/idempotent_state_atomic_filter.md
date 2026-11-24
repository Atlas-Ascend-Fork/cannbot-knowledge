---
type: Optimization
title: 单调完成状态过滤幂等原子更新
description: 对只需成功一次的状态标记，先局部去重并一致读取状态，跳过已经完成的全局 CAS。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.implementation.atomic
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/idempotent-state-atomic-filter.md
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
      "计数或累计等每次更新均有效的状态",
      "已有代表仍需被更早代表替换而未保留竞争"
    ],
    "required_conditions": [
      "状态每次调用只从空转为完成且不撤销",
      "已完成状态足以满足当前更新契约",
      "读取一致性与CAS竞争规则可证明"
    ]
  },
  "classification": "performance_strategy",
  "created": "2026-10-16",
  "feature_signature": {
    "bottleneck": [
      "duplicate-global-cas",
      "hot-occupied-slots"
    ],
    "pattern": "idempotent-state-atomic-filter"
  },
  "generality": "pattern",
  "id": "idempotent-state-atomic-filter",
  "implementation_steps": [
    "证明状态单调性，并分离需要代表替换的特殊键。",
    "初始化 seen bitmap，以原子置位或等价安全方法确定局部首个提交者。",
    "对可提前完成的键做一致读取，为 EMPTY 执行 CAS，其他键保留原竞争。",
    "按表容量和重复分布选择启用范围，比较完整调用。"
  ],
  "intent": "大量重复键集中到少数槽位，已占用后仍反复执行全局原子操作，热点竞争占主导。",
  "mechanism": "块内位图去重后，一致读取全局单调状态，仅仍为空时尝试CAS。",
  "name": "单调完成状态过滤幂等原子更新",
  "operator_scope": "占用表、去重标记及只需成功一次的完成位；重复率足够高，局部位图容量可接受，已完成代表满足当前契约。",
  "phase": [
    "design",
    "tuning"
  ],
  "principle": "状态若只由 EMPTY 变为 occupied，重复提交同一标记不会改变结果。可先用块内 seen bitmap 过滤重复键；赢得局部位的线程再用一致读取检查全局槽位，仅仍为 EMPTY 时执行 CAS。读到旧 EMPTY 只增加一次无效 CAS，CAS 仍仲裁竞争；读到 occupied 则可以跳过已无语义贡献的原子操作。关键是把幂等完成状态转为提前终止条件，而非修改原子指令本身。",
  "provenance": {
    "source_report": "AOA_skill PR#15 commit c7d842a"
  },
  "risks": [
    "本次调用内状态不能撤销或重新置空，表必须初始化并与其他调用隔离",
    "计数、求和、乘法等每次更新都有贡献的操作不可使用",
    "若 occupied 只是发布标记，载荷的发布与读取还须满足内存顺序，不能把看到标记等同于载荷可见",
    "asc_ldcg 等一致读取的适用地址与可见性须按目标平台确认；读到 EMPTY 后仍须 CAS",
    "seen bitmap 并发置位须防丢更新，初始化和同步必须全块一致",
    "合并等价键若要求最早原始代表，发现 occupied 仍可能需要更早索引竞争，必须保留对应 CAS 循环，不能让位图或已占用快路跳过它"
  ],
  "schema_version": 2,
  "slug": "idempotent-state-atomic-filter",
  "source": "aoa_skill_pr15",
  "status": "pending",
  "summary": "对只需成功一次的状态标记，先局部去重并一致读取状态，跳过已经完成的全局 CAS。",
  "verification": {
    "correctness": [
      "覆盖高低重复率、跨块热点、并发调用、等价键代表及尾部位图"
    ],
    "performance": [
      "检查无丢失标记、代表正确、同步一致；性能须包含位图初始化及新增读，不能只计算减少的 CAS 数量"
    ],
    "rollback_signals": [
      "状态可回收、版本变化或必须更新更优代表；局部位图太大或低重复率时退回直接原子路径",
      "不能依靠非一致普通读推断跨核完成"
    ]
  }
}
-->

# 性能优化策略：单调完成状态过滤幂等原子更新

单一优化点：对只需成功一次的状态标记，先局部去重并一致读取状态，跳过已经完成的全局 CAS。

## 1. 原理

状态若只由 EMPTY 变为 occupied，重复提交同一标记不会改变结果。可先用块内 seen bitmap 过滤重复键；赢得局部位的线程再用一致读取检查全局槽位，仅仍为 EMPTY 时执行 CAS。读到旧 EMPTY 只增加一次无效 CAS，CAS 仍仲裁竞争；读到 occupied 则可以跳过已无语义贡献的原子操作。关键是把幂等完成状态转为提前终止条件，而非修改原子指令本身。

## 2. 性能问题模式

大量重复键集中到少数槽位，已占用后仍反复执行全局原子操作，热点竞争占主导。局部去重先削减块内重复，全局一致读再削减跨块重复。新增位图初始化、局部原子置位、全局读及分支；低重复率或分散键可能无法摊薄这些成本。

## 3. 正确性红线

本次调用内状态不能撤销或重新置空，表必须初始化并与其他调用隔离。计数、求和、乘法等每次更新都有贡献的操作不可使用。若 occupied 只是发布标记，载荷的发布与读取还须满足内存顺序，不能把看到标记等同于载荷可见。asc_ldcg 等一致读取的适用地址与可见性须按目标平台确认；读到 EMPTY 后仍须 CAS。

seen bitmap 并发置位须防丢更新，初始化和同步必须全块一致。合并等价键若要求最早原始代表，发现 occupied 仍可能需要更早索引竞争，必须保留对应 CAS 循环，不能让位图或已占用快路跳过它。

## 4. 泛化条件

适用：占用表、去重标记及只需成功一次的完成位；重复率足够高，局部位图容量可接受，已完成代表满足当前契约。

不适用或需退回：状态可回收、版本变化或必须更新更优代表；局部位图太大或低重复率时退回直接原子路径。不能依靠非一致普通读推断跨核完成。

## 5. 实施步骤

1. 证明状态单调性，并分离需要代表替换的特殊键。
2. 初始化 seen bitmap，以原子置位或等价安全方法确定局部首个提交者。
3. 对可提前完成的键做一致读取，为 EMPTY 执行 CAS，其他键保留原竞争。
4. 按表容量和重复分布选择启用范围，比较完整调用。

## 6. LLM 前置问题

每次重复更新是否无贡献？完成位是否携带载荷发布语义？是否要求最早或最优代表？局部去重会不会屏蔽必要竞争？一致读在目标平台上是否成立？

## 7. 验收标准

覆盖高低重复率、跨块热点、并发调用、等价键代表及尾部位图。检查无丢失标记、代表正确、同步一致；性能须包含位图初始化及新增读，不能只计算减少的 CAS 数量。

## 8. 分类与证据

- Classification：`performance_strategy`
- Generality：`pattern`
- Related anti-patterns：无

- 尚无归档证据（provenance：AOA_skill PR#15 commit c7d842a）。

## 检索卡（短卡）

动作：先用块内seen bitmap去重，再一致读全局状态，仅EMPTY时尝试CAS。
适用：状态本次调用单调由空转完成、不撤销；已完成代表满足当前契约。
限制：计数或累计不可用；读空仍须CAS；载荷发布顺序须成立；最早代表要求保留竞争循环。
范围：占用表、去重及只需成功一次的状态标记。
检索词：idempotent、monotonic、asc_ldcg、CAS、seen bitmap、EMPTY
机会：热点槽已完成后仍被重复提交全局原子操作。
代价：位图初始化、局部置位、一致读和分支；低重复率可能回退。
