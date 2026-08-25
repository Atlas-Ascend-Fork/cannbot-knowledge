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

- [561103: isGroup=-1 哨兵致 tilingKey 路由失配](../../../../runbooks/compilation/561103_isgroup_1_tilingkey.md)（`exemplifies`）：561103: isGroup=-1 哨兵致 tilingKey 路由失配 与《REGISTER_TILING_FOR_TILINGKEY》的实质衔接是：该故障是 host tiling 上下文哨兵未覆盖，使 TilingKey 路由返回 -1；key 注册/判定/获取宏和位编码案例直接用于修复并与 361001 分派缺失区分。
- [ACLNN 361001 — tilingKey 与 funcEntry 映射失](../../../../runbooks/compilation/aclnn_361001_tilingkey_funcentry_sel_position.md)（`exemplifies`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《REGISTER_TILING_FOR_TILINGKEY》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [REGISTER_TILING_DEFAULT 取小档致 NaN](../../../../runbooks/compilation/register_tiling_default_nan.md)（`exemplifies`）：REGISTER_TILING_DEFAULT 取小档致 NaN 与《REGISTER_TILING_FOR_TILINGKEY》的实质衔接是：REGISTER_TILING_DEFAULT 决定 opParaSize，必须覆盖最大 TilingData struct；注册宏、GET 宏、host/kernel 结构、SetDataSize 与追加越界卡描述同一 buffer 尺寸链。
- [REGISTER_TILING_DEFAULT 多 struct 冲突](../../../../runbooks/compilation/register_tiling_default_struct.md)（`exemplifies`）：REGISTER_TILING_DEFAULT 多 struct 冲突 与《REGISTER_TILING_FOR_TILINGKEY》的实质衔接是：一个算子只能有一个 REGISTER_TILING_DEFAULT struct；新分支须按 TilingKey 注册，GET 宏、Host/Kernel struct、SetDataSize 与冲突故障共同约束 buffer 和 key。
- [TilingKey 缓存 correction 致 tilingdata 复用](../../../../runbooks/compilation/ge_tilingkey_cache_reuse_per_call_attr_pollution.md)（`exemplifies`）：TilingKey 缓存 correction 致 tilingdata 复用 与《REGISTER_TILING_FOR_TILINGKEY》的实质衔接是：该问题由 GE 按 TilingKey 缓存 correction 造成同 shape 调用复用旧 TilingData；属性传递指南和注册/判定宏共同说明如何让变化属性进入正确 tiling 分派。
- [多分支策略](../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/multi_branch_strategy.md)（`explains`）：多分支策略 与《REGISTER_TILING_FOR_TILINGKEY》的实质衔接是：多分支策略由 Host 选择 TilingKey、Kernel 用 TILING_KEY_IS 常量折叠；REGISTER_TILING_DEFAULT/FOR_TILINGKEY 绑定结构，GET_TILING_DATA 取参数，所选故障卡分别验证 key 编码、funcEntry、缓存和默认结构注册失配。
- [REGISTER_TILING_DEFAULT](register_tiling_default.md)（`related`）：当不同 TilingKey 需要不同结构体时应从唯一 default 槽切换到按 key 注册，正是多 struct 冲突的接口级替代契约。
- [TILING_KEY_IS](tiling_key_is.md)（`related`）：Host 选择的 TilingKey 不仅决定 TILING_KEY_IS 分支，还必须匹配该 key 注册的 TilingData 结构。
- [COPY_TILING_WITH_STRUCT](copy_tiling_with_struct.md)（`same_topic`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；REGISTER_TILING_FOR_TILINGKEY正文说明“用于在kernel侧注册与TilingKey相匹配的TilingData自定义结构体；该接口需提供一个逻辑表达式，逻辑表达式以字符串“TILING_KEY_VAR”代指实际TilingKey，表达TilingKey所满足的范围”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
- [TILING_KEY_LIST](tiling_key_list.md)（`same_topic`）：REGISTER_TILING_FOR_TILINGKEY说明用于在kernel侧注册与TilingKey相匹配的TilingData自定义结构体；该接口需提供一个逻辑表达式，逻辑表达式以字符串“TILING_KEY_VAR”代指实际TilingKey，表达TilingKey所满足的范围。
<!-- cannbot:related:end -->
