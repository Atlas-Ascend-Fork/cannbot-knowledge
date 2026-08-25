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

<!-- cannbot:related:start -->
## 相关

- [TQueBind](../../../../apis/simd_api/basic_api/resource_management/t_que_bind/t_que_bind.md)（`explains`）：纯搬运类算子VECIN和VECOUT建议复用 与《TQueBind》的实质衔接是：VECIN/VECOUT 复用依赖 TQueBind 将输入输出逻辑位置绑定到同一物理队列；高效搬运、UB 融合和优化总览说明这种复用减少搬运与 UB 占用的适用边界。
- [TQueBind](../../../../apis/simd_api/basic_api/resource_management/t_que_bind/t_que_bind_constructor.md)（`explains`）：纯搬运类算子VECIN和VECOUT建议复用 与《TQueBind》的实质衔接是：VECIN/VECOUT 复用依赖 TQueBind 将输入输出逻辑位置绑定到同一物理队列；高效搬运、UB 融合和优化总览说明这种复用减少搬运与 UB 占用的适用边界。
- [TQueBind简介](../../../../apis/simd_api/basic_api/resource_management/t_que_bind/t_que_bind_intro.md)（`explains`）：TQueBind简介 与《纯搬运类算子VECIN和VECOUT建议复用》的实质衔接是：TQueBind 与 TQue 的差别在绑定两队列；复用、EnQue 重载和 InitBuffer 故障卡直接约束该资源生命周期。
- [EfficientTransferApi](efficient_transfer_api.md)（`related`）：纯搬运类算子VECIN和VECOUT建议复用 与《EfficientTransferApi》的实质衔接是：VECIN/VECOUT 复用依赖 TQueBind 将输入输出逻辑位置绑定到同一物理队列；高效搬运、UB 融合和优化总览说明这种复用减少搬运与 UB 占用的适用边界。
- [优化建议总览表（SIMD算子优化）](../optimization_summary.md)（`related`）：纯搬运类算子VECIN和VECOUT建议复用 与《优化建议总览表（SIMD算子优化）》的实质衔接是：VECIN/VECOUT 复用依赖 TQueBind 将输入输出逻辑位置绑定到同一物理队列；高效搬运、UB 融合和优化总览说明这种复用减少搬运与 UB 占用的适用边界。
- [通过Unified Buffer融合实现连续vector计算](../vector_compute/ub_fusion_vector_compute.md)（`related`）：纯搬运类算子VECIN和VECOUT建议复用 与《通过Unified Buffer融合实现连续vector计算》的实质衔接是：VECIN/VECOUT 复用依赖 TQueBind 将输入输出逻辑位置绑定到同一物理队列；高效搬运、UB 融合和优化总览说明这种复用减少搬运与 UB 占用的适用边界。
<!-- cannbot:related:end -->
