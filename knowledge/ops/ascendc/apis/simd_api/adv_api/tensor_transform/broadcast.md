---
type: API
title: Broadcast（张量变换）
description: 将输入按照输出shape进行广播。 比如A的shape为\(2,1\)，广播的目标shape为\(2,16\)，则会将原来的一列扩展为相同的16列。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/tensor_transform/Broadcast.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Broadcast

将输入按照输出shape进行广播。例如将shape为(m,1)的数据广播到(m,k)，即将一列扩展为相同的k列。模板参数T支持half/float。

提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。临时空间大小通过GetBroadCastMaxMinTmpSize获取。接口参数：dstTensor输出广播结果；srcTensor输入数据；sharedTmpBuffer临时缓存；broadcastInfo含输入输出shape信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [AscendC Muls cyclic-repeat 致分组 scale 错配](../../../../runbooks/precision/ascendc_muls_cyclic_repeat_scale.md)（`exemplifies`）：AscendC Muls cyclic-repeat 致分组 scale 错配 与《Broadcast（张量变换）》的实质衔接是：Muls 对短 scale 做 cyclic repeat 而分组量化需要 block repeat；Broadcast、Muls、AntiQuant、GroupedMatmul/SwiGLU 案例共同验证 scale 的连续分组映射。
- [FindSplitAxis 误传 total_slots 致 slot 翻倍](../../../../runbooks/precision/findsplitaxis_total_slots_slot.md)（`exemplifies`）：FindSplitAxis 误传 total_slots 致 slot 翻倍 与《Broadcast（张量变换）》的实质衔接是：FindSplitAxis 第四参要求 phys_nodes，传入已乘 DB 的 total_slots 会再次乘二；per-buffer UB 预算、rank/split、TilingData 和 Broadcast 卡用于核对内外切分量一致。
- [MulPreferContiguous 稀疏广播拦截失败且慢于 304](../../../../runbooks/performance/mulprefercontiguous_304.md)（`exemplifies`）：《MulPreferContiguous 稀疏广播拦截失败且慢于 304》处理“B 类稀疏广播（首轴稀疏、stride 大）触发 MulPreferContiguous 拦截转连续，baseline GetWorkspaceSize 返回 -1.0（schMode 空）或性能慢于 fixed 直接走 304 nddma_transpose_noLoop。”。《Broadcast（张量变换）》提供“将输入按照输出shape进行广播。 比如A的shape为\(2,1\)，广播的目标shape为\(2,16\)，则会将原来的一列扩展为相同的16列。”，其具体合同或探针直接接入稀疏广播输入的 contiguous 拦截、304 路由和非连续 shape/stride 合同。
- [softplus_v2_grad tiling rank 校验拒标量广播](../../../../runbooks/compilation/softplus_v2_grad_tiling_rank.md)（`exemplifies`）：该 API 正文明确输入按目标 shape 广播，直接支撑 focal 中标量与高 rank tensor 不必原始 rank 相等、而应在目标 shape 上判断可广播性的结论。
- [反量化 561103 实为 CheckBroadcastShape 过严](../../../../runbooks/compilation/561103_checkbroadcastshape.md)（`exemplifies`）：Broadcast 高阶接口页定义输入/输出 shape 契约，是判断 561103 是否来自非法广播的直接依据。
- [Broadcast场景](../../../../guides/operator_practice/simd_operator_impl/vector_programming/broadcast_scenario.md)（`explains`）：指南中的 Compute 阶段直接调用 Broadcast 将短 shape 扩展后再做 Add，该 API 是方案的核心执行接口。
- [GetBroadCastMaxMinTmpSize](get_broad_cast_max_min_tmp_size.md)（`related`）：GetBroadCastMaxMinTmpSize 返回的缓存范围专供 Broadcast kernel 使用，shape、typeSize 和 isReuseSource 必须保持一致。
<!-- cannbot:related:end -->
