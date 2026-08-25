---
type: API
title: TSCM
description: TSCM接口索引页，包含简介、AllocTensor、FreeTensor、EnQue与DeQue。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TSCM/TSCM.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# TSCM

TSCM是数据通路目的地为TSCM Position时的队列管理结构，本质是TQueBind的别名（TQueBind<pos, TPosition::TSCM, depth, mask>），用于Vector与Cube之间的通信和同步。
模板参数pos支持VECIN、GM；depth推荐设置为1；mask的bit 2控制VECTOR0/VECTOR1在CUBE内存位置的映射关系（0为错开，1为相同）。
支持AllocTensor/EnQue/DeQue/FreeTensor完整生命周期，须严格配对使用，但不支持VacantInQue/HasTensorInQue等查询接口。常与Matmul高阶API配合使用，L1 Buffer(TSCM)从UB发起的Buffer块数量与Matmul对象数量之和最大为10个，超出可能引起未定义行为。

<!-- cannbot:related:start -->
## 相关

- [FreeTensor早释使队列别名被下一轮DMA覆盖](../../../../../runbooks/precision/reinterpret_tensor_alias_must_outlive_queue_release.md)（`exemplifies`）：TSCM 与《FreeTensor早释使队列别名被下一轮DMA覆盖》的实质衔接是：TSCM 的 Queue/Buffer 生命周期需要成对 Alloc/Free、EnQue/DeQue 与所有权交接；所选故障卡分别覆盖空取、早释、重取和跨流水复用。
- [PadMode/单参 EnQue 在 CANN9.0.0 编译失败](../../../../../runbooks/compilation/padmode_enque_cann9_0_0.md)（`exemplifies`）：TSCM 与《PadMode/单参 EnQue 在 CANN9.0.0 编译失败》的实质衔接是：TSCM 的 Queue/Buffer 生命周期需要成对 Alloc/Free、EnQue/DeQue 与所有权交接；所选故障卡分别覆盖空取、早释、重取和跨流水复用。
- [TQue 输入未释放导致循环 AllocTensor 卡死](../../../../../runbooks/compilation/tque_dequeue_must_end_with_freetensor.md)（`exemplifies`）：TSCM 与《TQue 输入未释放导致循环 AllocTensor 卡死》的实质衔接是：TSCM 的 Queue/Buffer 生命周期需要成对 Alloc/Free、EnQue/DeQue 与所有权交接；所选故障卡分别覆盖空取、早释、重取和跨流水复用。
- [TSCM输入的矩阵乘](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/tscm_input_matmul.md)（`explains`）：TSCM 与《TSCM输入的矩阵乘》的实质衔接是：TSCM 的 Queue/Buffer 生命周期需要成对 Alloc/Free、EnQue/DeQue 与所有权交接；所选故障卡分别覆盖空取、早释、重取和跨流水复用。
- [运行验证时AllocTensor/FreeTensor失败](../../../../../guides/programming_guide/appendix/faq/alloc_free_tensor_failure.md)（`explains`）：TSCM 与《运行验证时AllocTensor/FreeTensor失败》的实质衔接是：TSCM 的 Queue/Buffer 生命周期需要成对 Alloc/Free、EnQue/DeQue 与所有权交接；所选故障卡分别覆盖空取、早释、重取和跨流水复用。
- [DeQue](de_que.md)（`same_topic`）：DeQue 与《TSCM》的实质衔接是：TSCM DeQue 必须与 EnQue、Alloc/Free 和所有权交接配套；所选故障卡直接覆盖空队列、重复 DeQue、早释和跨流水交接。
- [TSCM简介](tscm_intro.md)（`same_topic`）：TSCM 与《TSCM简介》的实质衔接是：TSCM 的 Queue/Buffer 生命周期需要成对 Alloc/Free、EnQue/DeQue 与所有权交接；所选故障卡分别覆盖空取、早释、重取和跨流水复用。
<!-- cannbot:related:end -->
