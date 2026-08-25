---
type: API
title: GroupNorm
description: 对shape为[N,C,H,W]的输入，将每个[C,H,W]在C维度上分为groupNum组并对每一组进行标准化，再通过可训练的缩放参数γ和平移参数β进行调整。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/GroupNorm.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GroupNorm

对shape为[N, C, H, W]的输入，将每个[C, H, W]在C维度上分为groupNum组，对每一组进行标准化（计算均值和标准差），最后对标准化结果进行缩放（γ）和平移（β）。输出归一化结果、均值和方差。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过GroupNorm Tiling获取。模板参数isReuseSource预留（传false）。

接口参数：output输出归一化结果；outputMean/outputVariance输出均值和方差；inputX输入；gamma/beta输入缩放和平移系数；sharedTmpBuffer临时缓存；epsilon防除零系数；tiling切分信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：仅支持ND格式；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [ARA 多 group 共用 max/sum 污染后续输出](../../../../runbooks/precision/ara_group_statistics_must_reset_per_group.md)（`exemplifies`）：《GroupNorm》处理“对shape为[N,C,H,W]的输入，将每个[C,H,W]在C维度上分为groupNum组并对每一组进行标准化，再通过可训练的缩放参数γ和平移参数β进行调整。”。《ARA 多 group 共用 max/sum 污染后续输出》明确提供“ARA 三趟归约缓冲若只在 group 循环外初始化，后续 group 会继承前组 max/sum；应逐 group 重置再完成三趟。”，其参数、调用或验证步骤直接接入GroupNorm 的分组统计、Welford 计算、Tiling 与格式约束。
- [OpDef FORMAT_NCHW 致 5D 报 161002](../../../../runbooks/compilation/opdef_format_nchw_5d_161002.md)（`exemplifies`）：《GroupNorm》处理“对shape为[N,C,H,W]的输入，将每个[C,H,W]在C维度上分为groupNum组并对每一组进行标准化，再通过可训练的缩放参数γ和平移参数β进行调整。”。《OpDef FORMAT_NCHW 致 5D 报 161002》明确提供“同时支持 4D/5D 的算子在 OpDef 注册 FORMAT_NCHW 会让 5D 张量在 GetWorkspaceSize 阶段报 ACLNN error 161002；NCHW 只对 4D 有效，该路线 banned，应保持 FORMAT_ND 并由 tiling 据 shape 推断布局。”，其参数、调用或验证步骤直接接入GroupNorm 的分组统计、Welford 计算、Tiling 与格式约束。
- [WelfordFinalize](welford_finalize.md)（`related`）：《GroupNorm》处理“对shape为[N,C,H,W]的输入，将每个[C,H,W]在C维度上分为groupNum组并对每一组进行标准化，再通过可训练的缩放参数γ和平移参数β进行调整。”。《WelfordFinalize》明确提供“Welford算法的后处理接口，用于在线计算均值和方差的最终结果。LayerNorm中Reduce轴较大时可切分Reduce轴，联合WelfordUpdate实现等效计算LayerNorm。”，其参数、调用或验证步骤直接接入GroupNorm 的分组统计、Welford 计算、Tiling 与格式约束。
- [WelfordFinalize Tiling](welford_finalize_tiling.md)（`related`）：《GroupNorm》处理“对shape为[N,C,H,W]的输入，将每个[C,H,W]在C维度上分为groupNum组并对每一组进行标准化，再通过可训练的缩放参数γ和平移参数β进行调整。”。《WelfordFinalize Tiling》明确提供“获取WelfordFinalize kernel计算时所需的Tiling参数，通过GetWelfordFinalizeMaxMinTmpSize获取接口计算所需最大和最小临时空间大小。”，其参数、调用或验证步骤直接接入GroupNorm 的分组统计、Welford 计算、Tiling 与格式约束。
- [WelfordUpdate](welford_update.md)（`related`）：《GroupNorm》处理“对shape为[N,C,H,W]的输入，将每个[C,H,W]在C维度上分为groupNum组并对每一组进行标准化，再通过可训练的缩放参数γ和平移参数β进行调整。”。《WelfordUpdate》明确提供“Welford算法的前处理接口，用于在线逐步计算均值和方差中间结果。LayerNorm中Reduce轴较大时可切分Reduce轴，联合WelfordFinalize实现等效计算LayerNorm。”，其参数、调用或验证步骤直接接入GroupNorm 的分组统计、Welford 计算、Tiling 与格式约束。
- [WelfordUpdate Tiling](welford_update_tiling.md)（`related`）：《GroupNorm》处理“对shape为[N,C,H,W]的输入，将每个[C,H,W]在C维度上分为groupNum组并对每一组进行标准化，再通过可训练的缩放参数γ和平移参数β进行调整。”。《WelfordUpdate Tiling》明确提供“获取WelfordUpdate kernel计算时所需的Tiling参数，通过GetWelfordUpdateMaxMinTmpSize获取接口计算所需最大和最小临时空间大小。”，其参数、调用或验证步骤直接接入GroupNorm 的分组统计、Welford 计算、Tiling 与格式约束。
- [GroupNorm Tiling](group_norm_tiling.md)（`same_topic`）：《GroupNorm》处理“对shape为[N,C,H,W]的输入，将每个[C,H,W]在C维度上分为groupNum组并对每一组进行标准化，再通过可训练的缩放参数γ和平移参数β进行调整。”。《GroupNorm Tiling》明确提供“获取GroupNorm kernel计算时所需的Tiling参数，包括通过GetGroupNormMaxMinTmpSize获取最大最小临时空间大小和GetGroupNormNDTilingInfo获取tiling参数。”，其参数、调用或验证步骤直接接入GroupNorm 的分组统计、Welford 计算、Tiling 与格式约束。
<!-- cannbot:related:end -->
