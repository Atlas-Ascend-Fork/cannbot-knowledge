---
type: API
title: TILING_KEY_IS
description: 在核函数中判断本次执行时的tiling_key是否等于host侧运行时设置的某个key，从而标识tiling_key==key的一条kernel分支。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/TILING_KEY_IS.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TILING_KEY_IS

在核函数中判断本次执行的 tiling_key 是否等于 host 侧设置的某个 key，标识 tiling_key==key 的 kernel 分支。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [561103: isGroup=-1 哨兵致 tilingKey 路由失配](../../../../runbooks/compilation/561103_isgroup_1_tilingkey.md)（`exemplifies`）：561103: isGroup=-1 哨兵致 tilingKey 路由失配 与《TILING_KEY_IS》的实质衔接是：该故障是 host tiling 上下文哨兵未覆盖，使 TilingKey 路由返回 -1；key 注册/判定/获取宏和位编码案例直接用于修复并与 361001 分派缺失区分。
- [ACLNN 361001 — tilingKey 与 funcEntry 映射失](../../../../runbooks/compilation/aclnn_361001_tilingkey_funcentry_sel_position.md)（`exemplifies`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《TILING_KEY_IS》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [TilingKey 缓存 correction 致 tilingdata 复用](../../../../runbooks/compilation/ge_tilingkey_cache_reuse_per_call_attr_pollution.md)（`exemplifies`）：TilingKey 缓存 correction 致 tilingdata 复用 与《TILING_KEY_IS》的实质衔接是：该问题由 GE 按 TilingKey 缓存 correction 造成同 shape 调用复用旧 TilingData；属性传递指南和注册/判定宏共同说明如何让变化属性进入正确 tiling 分派。
- [tilingKey 编码与 TPL 位打包不一致致路由错误](../../../../runbooks/compilation/tiling_key_tpl_bit_encoding_mismatch.md)（`exemplifies`）：该 runbook 给出 Host 语义编号与模板位打包编码不一致时分支路由错误的确定诊断，直接验证 key 判定契约。
- [多分支策略](../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/multi_branch_strategy.md)（`explains`）：多分支策略 与《TILING_KEY_IS》的实质衔接是：多分支策略由 Host 选择 TilingKey、Kernel 用 TILING_KEY_IS 常量折叠；REGISTER_TILING_DEFAULT/FOR_TILINGKEY 绑定结构，GET_TILING_DATA 取参数，所选故障卡分别验证 key 编码、funcEntry、缓存和默认结构注册失配。
- [ASCENDC_TPL_SEL_PARAM](../../../utils_api/tiling_template_programming/ascendc_tpl_sel_param.md)（`related`）：ASCENDC_TPL_SEL_PARAM 与《TILING_KEY_IS》的实质衔接是：TPL 参数必须与模板定义、GET_TPL_TILING_KEY 和 TILING_KEY_IS 位编码一致；所选故障卡覆盖缺宏、头文件、funcEntry 和缓存复用失配。
- [IcpuSetTilingKey](../debug_interface/cpu_twin_debug/icpu_set_tiling_key.md)（`related`）：IcpuSetTilingKey 与《TILING_KEY_IS》的实质衔接是：IcpuSetTilingKey 只在 CPU 孪生调试中选择 IcpuRunKf 的 kernel 分支；TILING_KEY 宏及路由故障卡直接约束编码、缓存和 funcEntry 映射。
- [REGISTER_TILING_FOR_TILINGKEY](register_tiling_for_tilingkey.md)（`related`）：Host 选择的 TilingKey 不仅决定 TILING_KEY_IS 分支，还必须匹配该 key 注册的 TilingData 结构。
- [TILING_KEY_LIST](tiling_key_list.md)（`same_topic`）：TILING_KEY_IS说明在核函数中判断本次执行时的tiling_key是否等于host侧运行时设置的某个key，从而标识tiling_key==key的一条kernel分支。
<!-- cannbot:related:end -->
