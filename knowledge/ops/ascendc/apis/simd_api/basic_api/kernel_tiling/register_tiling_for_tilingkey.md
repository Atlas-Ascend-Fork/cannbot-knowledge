---
type: API
title: REGISTER_TILING_FOR_TILINGKEY
description: 用于在kernel侧注册与TilingKey相匹配的TilingData自定义结构体；该接口需提供一个逻辑表达式，逻辑表达式以字符串“TILING_KEY_VAR”代指实际TilingKey，表达TilingKey所满足的范围。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/REGISTER_TILING_FOR_TILINGKEY.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# REGISTER_TILING_FOR_TILINGKEY

在 kernel 侧注册与 TilingKey 相匹配的 TilingData 结构体。提供逻辑表达式（以 TILING_KEY_VAR 代指实际 TilingKey）表达 TilingKey 满足的范围。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [REGISTER_TILING_DEFAULT 取小档致 NaN](../../../../runbooks/compilation/register_tiling_default_nan.md)（`exemplifies`）：提供逻辑表达式（以 TILING_KEY_VAR 代指实际 TilingKey）表达 TilingKey 满足的范围；`REGISTER_TILING_FOR_TILINGKEY` 不会把 opParaSize 抬到大档。接口卡说明该宏负责 key 到结构的注册，运行手册补充其不会决定全局 opParaSize 上界，防止把按 key 注册误当成大结构容量修复。
- [REGISTER_TILING_DEFAULT 多 struct 冲突](../../../../runbooks/compilation/register_tiling_default_struct.md)（`exemplifies`）：在 kernel 侧注册与 TilingKey 相匹配的 TilingData 结构体；将 separable 分支的 `REGISTER_TILING_DEFAULT(MaxPool3DGradSeparableTilingData)` 改为 `REGISTER_TILING_FOR_TILINGKEY(<key 字符串>, MaxPool3DGradSeparableTilingData)` 后重新构建，该报错消失、binary 生成恢复。接口卡定义按 TilingKey 注册独立结构，运行手册以多分支 default 槽冲突的真实构建证明该宏是新增结构分支的直接修法。
- [TILING_KEY_IS](tiling_key_is.md)（`same_topic`）：判断本次执行的 tiling_key 是否等于 host 侧设置的某个 key；注册与 TilingKey 相匹配的 TilingData 结构体。REGISTER_TILING_FOR_TILINGKEY 先把 key 条件映射到 TilingData，TILING_KEY_IS 再在 kernel 中选择相同 key 的执行分支；两者共同保证数据结构和代码分支匹配。
<!-- cannbot:related:end -->
