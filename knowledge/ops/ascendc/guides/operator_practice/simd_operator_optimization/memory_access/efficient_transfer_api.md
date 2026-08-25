---
type: Guide
title: EfficientTransferApi
description: 使用搬运API时应通过配置搬运控制参数实现连续或固定间隔搬运，避免使用for循环，提升搬运效率。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/efficient_transfer_api.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 高效的使用搬运API

【优先级】高
【描述】在使用搬运API时，应该尽可能地通过配置搬运控制参数实现连续搬运或者固定间隔搬运，避免使用for循环，二者效率差距极大。如下图示例，图片的每一行为16KB，需要从每一行中搬运前2KB，针对这种场景，使用for循环遍历每行，每次仅能搬运2KB。若直接配置DataCopyParams参数（包含srcStride/dstStride/blockLen/blockCount），则可以达到一次搬完的效果，每次搬运32KB；参考尽量一次搬运较大的数据块章节介绍的搬运数据量和实际带宽的关系，建议一次搬完。
【反例】
【正例】

<!-- cannbot:related:start -->
## 相关

- [UB与UB数据搬运](../../../../apis/simd_api/basic_api/data_move_guide/ub_ub_data_move.md)（`explains`）：焦点处理UB 数据搬运的性能与流水实现边界；EfficientTransferApi正文界定“使用搬运API时应通过配置搬运控制参数实现连续或固定间隔搬运，避免使用for循环，提升搬运效率”。候选给出循环 SetGlobalBuffer、有效搬运 API 和 TQue 双缓冲的具体性能边界，而非罗列所有搬运成员。
- [DataCopyExtParams blockLen 窄化编译失败](../../../../runbooks/compilation/datacopyextparams_block_len_requires_uint32.md)（`related`）：EfficientTransferApi：指南要求用DataCopyExtParams一次表达blockCount/blockLen/stride；相邻搬运指南解释非连续与大块策略，blockLen类型runbook和NDDMA dstStride卡给出参数落地时的编译/偏移验证。 目标卡《DataCopyExtParams blockLen 窄化编译失败》补充：DataCopyExtParams 的 blockLen 接收 uint32_t，模板表达式 D* sizeof(T) 须显式窄化后再做 DataCopyPad。
- [NDDMA多维dstStride致data搬运偏移的判别](../../../../runbooks/precision/nddma_dststride_data.md)（`related`）：EfficientTransferApi：指南要求用DataCopyExtParams一次表达blockCount/blockLen/stride；相邻搬运指南解释非连续与大块策略，blockLen类型runbook和NDDMA dstStride卡给出参数落地时的编译/偏移验证。 目标卡《NDDMA多维dstStride致data搬运偏移的判别》补充：Ascend950PR 上 NDDMA nddma_out_to_ub_b32 在 RANK=4 模板 2+ 实际维度时 loopDstStride 被硬件错误应用致 GM→UB data 搬运偏移；1 维通过、2+ 维偏移，GetValue 探针与 NddmaDispatch 对比定位。
- [尽量一次搬运较大的数据块](transfer_larger_data_blocks.md)（`related`）：高效搬运接口页提供合并连续 block 所需的 DataCopy/NDDMA 选型与参数。
- [纯搬运类算子VECIN和VECOUT建议复用](vecin_vecout_reuse.md)（`related`）：纯搬运类算子VECIN和VECOUT建议复用 与《EfficientTransferApi》的实质衔接是：VECIN/VECOUT 复用依赖 TQueBind 将输入输出逻辑位置绑定到同一物理队列；高效搬运、UB 融合和优化总览说明这种复用减少搬运与 UB 占用的适用边界。
- [MemoryAccessMerge](../../simt_operator_optimization/memory_access/memory_access_merge.md)（`same_topic`）：《MemoryAccessMerge》处理“SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。”。《EfficientTransferApi》提供“使用搬运API时应通过配置搬运控制参数实现连续或固定间隔搬运，避免使用for循环，提升搬运效率。”，其具体合同或探针直接接入Warp 连续 GM 访问的短向量、类型对齐、步长搬运和 Gather 示例验证。
- [非对齐场景减少无效数据的搬运](reduce_invalid_data_transfer.md)（`same_topic`）：EfficientTransferApi：指南要求用DataCopyExtParams一次表达blockCount/blockLen/stride；相邻搬运指南解释非连续与大块策略，blockLen类型runbook和NDDMA dstStride卡给出参数落地时的编译/偏移验证。 目标卡《非对齐场景减少无效数据的搬运》补充：>该性能优化建议适用于如下型号：
- [非连续搬运场景减少搬运次数](reduce_non_contiguous_transfer.md)（`same_topic`）：两篇指南都要求把非连续数据搬运编码为单次 DataCopy 参数，而非逐块循环调用；一篇给出 blockCount/blockLen/stride 原则，另一篇给出 DataCopyPad Loop 与 NDDMA 实例。
<!-- cannbot:related:end -->
