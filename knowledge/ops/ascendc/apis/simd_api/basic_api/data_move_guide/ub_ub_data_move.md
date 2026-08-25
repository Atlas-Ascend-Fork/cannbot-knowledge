---
type: API
title: UB与UB数据搬运
description: Unified Buffer（UB）之间的数据搬运提供了灵活的接口支持，共有两组接口：DataCopy提供了基础的数据搬运能力，支持连续和非连续数据搬运；Copy除了支持连续和非连续数据搬运，还提供了mask操作和DataBlock间隔操作的能力，支持在接口内部和接口外部设置mask。具体接口功能如下表所示。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/UB_UB_data_move.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# UB与UB数据搬运

Unified Buffer 间数据搬运提供两组接口。DataCopy 支持连续和高维切分（DataCopyParams：blockCount/blockLen/srcGap/dstGap）搬运。Copy 除连续和高维切分外，还支持 mask 操作（SetVectorMask）和 DataBlock 间隔操作（srcStride/dstStride 以 DataBlock 为单位），可在接口内部或外部设置 mask。UB 地址需 32B 对齐。

<!-- cannbot:related:start -->
## 相关

- [HardSwish 逐元素 kernel 的 TQue 双缓冲实现配方](../../../../runbooks/compilation/elementwise_tque_double_buffer_inplace_recipe.md)（`exemplifies`）：焦点处理UB 数据搬运的性能与流水实现边界；HardSwish 逐元素 kernel 的 TQue 双缓冲实现配方正文界定“ascend910b 上 HardSwish 算子的可复用实现：2 个 TQue in-place、单 tile 快速路径、5 指令序列、remainder 均衡分块；15 测试点全部 Pass”。候选给出循环 SetGlobalBuffer、有效搬运 API 和 TQue 双缓冲的具体性能边界，而非罗列所有搬运成员。
- [Vector Sub 源 UB 非 32B 对齐触发错误 340](../../../../runbooks/compilation/vector_sub_ub_32b_340.md)（`exemplifies`）：Vector Sub 源 UB 非 32B 对齐触发错误 340 与《UB与UB数据搬运》的实质衔接是：Vector Sub 的每个 UB 源必须 32B 对齐，LocalTensor 非零 operator[] 偏移会破坏对齐；Sub API、GetWithOffset/TBuf 和相邻未对齐故障卡直接支持定位及对齐搬入修法。
- [EfficientTransferApi](../../../../guides/operator_practice/simd_operator_optimization/memory_access/efficient_transfer_api.md)（`explains`）：焦点处理UB 数据搬运的性能与流水实现边界；EfficientTransferApi正文界定“使用搬运API时应通过配置搬运控制参数实现连续或固定间隔搬运，避免使用for循环，提升搬运效率”。候选给出循环 SetGlobalBuffer、有效搬运 API 和 TQue 双缓冲的具体性能边界，而非罗列所有搬运成员。
- [Copy](../memory_vector_compute/data_move/copy_ub_to_ub_continuous.md)（`related`）：Copy 与《UB与UB数据搬运》的实质衔接是：该 Copy 是 32B 对齐的 UB 连续搬运；DataCopy 对应入口、UB-UB 搬运指南、AscCopy 与非 VL 掩码故障共同说明通路、对齐和尾块边界。
- [数据搬运导览](data_move_guide.md)（`related`）：《数据搬运导览》说明数据搬运导览，按 GM/UB/L1/L0/L0C 等路径组织 AscendC 基础 API 数据搬运接口的索引。；《UB与UB数据搬运》说明Unified Buffer（UB）之间的数据搬运提供了灵活的接口支持，共有两组接口：DataCopy提供了基础的数据搬运能力，支持连续和非连续数据搬运；Copy除了支持连续和非连续数据搬运，还提供了mask操作和DataBlock间隔操作的能力，支持在接口内部和接口外部设置mask。具体接口功能如下表所示。。二者在导览按GM、UB、L1、L0和L0C通路组织搬运选择，并以数据通路和对齐约束解释各子路径上存在可执行的直接衔接。
- [AscCopy](../../c_api/vector_compute/asc_copy.md)（`same_topic`）：AscCopy 与《UB与UB数据搬运》的实质衔接是：AscCopy 是 UB→UB 搬运；basic Copy、UB 搬运指南和 Reg Copy提供连续、高维/掩码入口，非整 VL 的 fp32 案例说明何时必须改用 masked Reg load/store。
- [Copy](../memory_vector_compute/data_move/copy_ub_to_ub_mask_highdim_split.md)（`same_topic`）：Copy 与《UB与UB数据搬运》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
<!-- cannbot:related:end -->
