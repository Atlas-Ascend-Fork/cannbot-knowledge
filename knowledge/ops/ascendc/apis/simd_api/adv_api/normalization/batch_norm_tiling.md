---
type: API
title: BatchNorm Tiling
description: 获取BatchNorm kernel计算时所需的Tiling参数，包括通过GetBatchNormMaxMinTmpSize获取最大最小临时空间大小和GetBatchNormNDTilingInfo获取tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/BatchNorm-Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# BatchNorm Tiling

host侧Tiling接口，用于获取BatchNorm kernel计算所需的Tiling参数，分两步：通过GetBatchNormMaxMinTmpSize获取最大和最小临时空间大小（minValue保证功能正确，maxValue提升性能）；通过GetBatchNormNDTilingInfo获取kernel侧所需tiling参数（含切分信息、临时空间位置等），开发者无需关注tiling结构体细节，直接传入BatchNorm高阶API使用。

GetBatchNormMaxMinTmpSize参数：ascendcPlatform平台信息；srcShape输入shape；typeSize数据类型字节数；isReuseSource预留传false；maxValue/minValue输出临时空间范围。

GetBatchNormNDTilingInfo参数：ascendcPlatform平台信息；srcShape(B,S,H)输入shape；typeSize数据类型字节数；isBasicBlock是否基本块；maxTmpSize可用临时空间；tiling输出BatchNormTiling结构体。约束：需保证B、S、H均大于0且S*H满足32B对齐。

<!-- cannbot:related:start -->
## 相关

- [EMA 公式 stat+m*(batch-stat) 在 inf 时 NaN](../../../../runbooks/precision/ema_stat_m_batch_stat_inf_nan.md)（`exemplifies`）：《BatchNorm Tiling》的任务是“获取BatchNorm kernel计算时所需的Tiling参数，包括通过GetBatchNormMaxMinTmpSize获取最大最小临时空间大小和GetBatchNormNDTilingInfo获取tiling参数。”。《EMA 公式 stat+m*(batch-stat) 在 inf 时 NaN》具体提供“bn_training_update 的 S10/S11 EMA 步用 stat+m*(batch-stat) 形式，当 mean/variance=±inf、batch 为有限值时 inf+(-inf)=NaN 污染 runningMean/runningVariance；golden 的 (1-m)*stat+m*batch 在 inf 时保持 inf，二者数学等价但 IEEE 754 不等价。”，它直接用于BatchNorm Tiling 所依赖的 Welford 统计量和数据格式约束。
- [OpDef FORMAT_NCHW 致 5D 报 161002](../../../../runbooks/compilation/opdef_format_nchw_5d_161002.md)（`exemplifies`）：《BatchNorm Tiling》的任务是“获取BatchNorm kernel计算时所需的Tiling参数，包括通过GetBatchNormMaxMinTmpSize获取最大最小临时空间大小和GetBatchNormNDTilingInfo获取tiling参数。”。《OpDef FORMAT_NCHW 致 5D 报 161002》具体提供“同时支持 4D/5D 的算子在 OpDef 注册 FORMAT_NCHW 会让 5D 张量在 GetWorkspaceSize 阶段报 ACLNN error 161002；NCHW 只对 4D 有效，该路线 banned，应保持 FORMAT_ND 并由 tiling 据 shape 推断布局。”，它直接用于BatchNorm Tiling 所依赖的 Welford 统计量和数据格式约束。
- [WelfordFinalize](welford_finalize.md)（`related`）：《BatchNorm Tiling》的任务是“获取BatchNorm kernel计算时所需的Tiling参数，包括通过GetBatchNormMaxMinTmpSize获取最大最小临时空间大小和GetBatchNormNDTilingInfo获取tiling参数。”。《WelfordFinalize》具体提供“Welford算法的后处理接口，用于在线计算均值和方差的最终结果。LayerNorm中Reduce轴较大时可切分Reduce轴，联合WelfordUpdate实现等效计算LayerNorm。”，它直接用于BatchNorm Tiling 所依赖的 Welford 统计量和数据格式约束。
- [WelfordFinalize Tiling](welford_finalize_tiling.md)（`related`）：《BatchNorm Tiling》的任务是“获取BatchNorm kernel计算时所需的Tiling参数，包括通过GetBatchNormMaxMinTmpSize获取最大最小临时空间大小和GetBatchNormNDTilingInfo获取tiling参数。”。《WelfordFinalize Tiling》具体提供“获取WelfordFinalize kernel计算时所需的Tiling参数，通过GetWelfordFinalizeMaxMinTmpSize获取接口计算所需最大和最小临时空间大小。”，它直接用于BatchNorm Tiling 所依赖的 Welford 统计量和数据格式约束。
- [WelfordUpdate](welford_update.md)（`related`）：《BatchNorm Tiling》的任务是“获取BatchNorm kernel计算时所需的Tiling参数，包括通过GetBatchNormMaxMinTmpSize获取最大最小临时空间大小和GetBatchNormNDTilingInfo获取tiling参数。”。《WelfordUpdate》具体提供“Welford算法的前处理接口，用于在线逐步计算均值和方差中间结果。LayerNorm中Reduce轴较大时可切分Reduce轴，联合WelfordFinalize实现等效计算LayerNorm。”，它直接用于BatchNorm Tiling 所依赖的 Welford 统计量和数据格式约束。
- [WelfordUpdate Tiling](welford_update_tiling.md)（`related`）：《BatchNorm Tiling》的任务是“获取BatchNorm kernel计算时所需的Tiling参数，包括通过GetBatchNormMaxMinTmpSize获取最大最小临时空间大小和GetBatchNormNDTilingInfo获取tiling参数。”。《WelfordUpdate Tiling》具体提供“获取WelfordUpdate kernel计算时所需的Tiling参数，通过GetWelfordUpdateMaxMinTmpSize获取接口计算所需最大和最小临时空间大小。”，它直接用于BatchNorm Tiling 所依赖的 Welford 统计量和数据格式约束。
- [BatchNorm](batch_norm.md)（`same_topic`）：《BatchNorm Tiling》的任务是“获取BatchNorm kernel计算时所需的Tiling参数，包括通过GetBatchNormMaxMinTmpSize获取最大最小临时空间大小和GetBatchNormNDTilingInfo获取tiling参数。”。《BatchNorm》具体提供“对每一层输入做规范化处理，在batch维度上计算均值和方差进行归一化，再通过缩放和平移参数调整分布，加速训练并提升泛化能力。”，它直接用于BatchNorm Tiling 所依赖的 Welford 统计量和数据格式约束。
<!-- cannbot:related:end -->
