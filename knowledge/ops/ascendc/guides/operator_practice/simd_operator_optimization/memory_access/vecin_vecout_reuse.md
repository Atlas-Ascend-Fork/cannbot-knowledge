---
type: Guide
title: 纯搬运类算子VECIN和VECOUT建议复用
description: 【描述】纯搬运类算子在执行时并不涉及实际vector计算，若存在冗余的vector指令，会导致算子整体执行时间变长。这种场景可以使用Ascend
  C针对纯搬运类算子提供的TQueBind接口，该接口可以将UB（VECIN）与UB（VECOUT）绑定，省略将数据从UB（VECIN）拷贝到UB（VECOUT）的步骤，从而避免vector的无谓消耗。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/vecin_vecout_reuse.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 纯搬运类算子VECIN和VECOUT建议复用

【优先级】高
【描述】纯搬运类算子在执行时并不涉及实际vector计算，若存在冗余的vector指令，会导致算子整体执行时间变长。这种场景可以使用Ascend C针对纯搬运类算子提供的TQueBind接口，该接口可以将UB（VECIN）与UB（VECOUT）绑定，省略将数据从UB（VECIN）拷贝到UB（VECOUT）的步骤，从而避免vector的无谓消耗。
【反例】
此段代码为了保证数据搬入和数据搬出之间的流水同步，存在LocalTensor -> LocalTensor的DataCopy指令。
【正例】
将LocalTensor -> LocalTensor的DataCopy指令替换为TQueBind接口，减少将UB（VECIN）拷贝到UB（VECOUT）的步骤，从而避免了冗余拷贝。
【性能对比】
如上图所示，将反例中DataCopy指令替换为TQueBind之后有明显优化。由于省略了数据从UB（VECIN）拷贝到UB（VECOUT）的步骤，aiv_vec_time几乎缩减为0。
