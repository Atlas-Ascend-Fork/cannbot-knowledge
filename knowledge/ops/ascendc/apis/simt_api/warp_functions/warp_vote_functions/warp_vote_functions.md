---
type: API
title: Warp Vote类函数
description: 提供Warp级别的投票与掩码接口。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_vote_functions/Warp_vote_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# Warp Vote类函数

提供 Warp 内的投票表决接口，包括全量判定（asc_all）、任一判定（asc_any）、位掩码收集（asc_ballot）和活跃掩码获取（asc_activemask）。这些函数对 Warp 内所有活跃 Lane 的布尔条件进行聚合，返回 Warp 级别的判定结果或位掩码，用于条件分支优化。

<!-- cannbot:related:start -->
## 相关

- [同一Warp内避免分支跳转](../../../../guides/operator_practice/simt_operator_optimization/control_flow/avoid_warp_branch.md)（`explains`）：Warp Vote类函数 与《同一Warp内避免分支跳转》的实质衔接是：该页自身仅列出 warp vote 成员，成员层级已由 part_of 表达；只保留直接使用 vote 做分支优化的指南及 cooperative-group Ballot 对照。
- [Ballot](../../cooperative_groups/coalesced_group/ballot.md)（`related`）：Warp Vote类函数 与《Ballot》的实质衔接是：该页自身仅列出 warp vote 成员，成员层级已由 part_of 表达；只保留直接使用 vote 做分支优化的指南及 cooperative-group Ballot 对照。
- [Ballot](../../cooperative_groups/thread_block_tile/ballot.md)（`related`）：Warp Vote类函数 与《Ballot》的实质衔接是：该页自身仅列出 warp vote 成员，成员层级已由 part_of 表达；只保留直接使用 vote 做分支优化的指南及 cooperative-group Ballot 对照。
- [Warp函数](../warp_functions_intro.md)（`related`）：概述明确 Vote 用于条件汇总和活跃掩码，专项页给出具体谓词与位图接口。
- [asc_any](asc_any.md)（`related`）：《asc_any》说明判断是否有活跃线程的输入不为0。 当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，所有活跃线程的predicate均为0，返回0，否则返回1。Warp内所有活跃线程返回相同的结果。；《Warp Vote类函数》说明提供Warp级别的投票与掩码接口。。二者在asc_any对Warp活跃线程做投票，与all/ballot/activemask共同定义聚合谓词并影响分支收敛上存在可执行的直接衔接。
- [asc_all](asc_all.md)（`same_topic`）：asc_all 与《Warp Vote类函数》的实质衔接是：asc_all 对活跃 warp predicate 做全真归约，any/ballot/activemask 与 cooperative-group all 是返回形式和作用域的直接对照。
<!-- cannbot:related:end -->
