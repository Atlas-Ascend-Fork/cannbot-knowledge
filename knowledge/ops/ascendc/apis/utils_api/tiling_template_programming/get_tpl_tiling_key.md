---
type: API
title: GET_TPL_TILING_KEY
description: Tiling模板编程时，开发者通过调用此接口自动生成TilingKey。该接口将传入的模板参数通过定义的位宽，转成二进制，按照顺序组合后转成uint64数值，即TilingKey。
  使用该接口需要包含定义模板参数和模板参数组合的头文件。详细内容请参考Tiling模板编程。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_template_programming/GET_TPL_TILING_KEY.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# GET_TPL_TILING_KEY

## 功能说明
Tiling模板编程时，开发者通过调用此接口自动生成TilingKey。该接口将传入的模板参数通过定义的位宽，转成二进制，按照顺序组合后转成uint64数值，即TilingKey。
使用该接口需要包含定义模板参数和模板参数组合的头文件。详细内容请参考Tiling模板编程。
## 函数原型
## 参数说明
## 返回值说明
TilingKey数值。
## 约束说明
无。

<!-- cannbot:related:start -->
## 相关

- [561103: isGroup=-1 哨兵致 tilingKey 路由失配](../../../runbooks/compilation/561103_isgroup_1_tilingkey.md)（`exemplifies`）：561103: isGroup=-1 哨兵致 tilingKey 路由失配 与《GET_TPL_TILING_KEY》的实质衔接是：该故障是 host tiling 上下文哨兵未覆盖，使 TilingKey 路由返回 -1；key 注册/判定/获取宏和位编码案例直接用于修复并与 361001 分派缺失区分。
- [ACLNN 361001 — tilingKey 与 funcEntry 映射失](../../../runbooks/compilation/aclnn_361001_tilingkey_funcentry_sel_position.md)（`exemplifies`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《GET_TPL_TILING_KEY》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [TilingKey 缓存 correction 致 tilingdata 复用](../../../runbooks/compilation/ge_tilingkey_cache_reuse_per_call_attr_pollution.md)（`exemplifies`）：TilingKey 缓存 correction 致 tilingdata 复用 与《GET_TPL_TILING_KEY》的实质衔接是：该问题由 GE 按 TilingKey 缓存 correction 造成同 shape 调用复用旧 TilingData；属性传递指南和注册/判定宏共同说明如何让变化属性进入正确 tiling 分派。
- [kernel.h 须 include struct.h 才能识别 TPL](../../../runbooks/compilation/ascendc_tpl_kernel_h_must_include_struct_h.md)（`exemplifies`）：Runbook 中 Host 用 GET_TPL_TILING_KEY 选择 RANK 分档，API 页定义该宏对 selection 的 tilingKey 编码契约。
- [sub-kernel 后缀 _N 是 tilingKey 位编码非序号](../../../runbooks/compilation/sub_kernel_n_tilingkey.md)（`exemplifies`）：官方 API 明确模板参数按各自位宽和声明顺序组合成 uint64 TilingKey，直接支撑 focal 对后缀位编码而非连续序号的解释。
- [tilingKey 编码与 TPL 位打包不一致致路由错误](../../../runbooks/compilation/tiling_key_tpl_bit_encoding_mismatch.md)（`exemplifies`）：tilingKey 编码与 TPL 位打包不一致致路由错误：这些卡沿同一 TPL 路由链闭合：GET_TPL_TILING_KEY按位编码，host funcEntry必须使用相同值，sub-kernel后缀展示实际编码，ASCENDC_TPL_SEL缺失或 isGroup哨兵会在相邻环节产生同类错路由。 目标卡《GET_TPL_TILING_KEY》补充：Tiling模板编程时，开发者通过调用此接口自动生成TilingKey。该接口将传入的模板参数通过定义的位宽，转成二进制，按照顺序组合后转成uint64数值，即TilingKey。 使用该接口需要包含定义模板参数和模板参数组合的头文件。详细内容请参考Tiling模板编程。
- [缺 ASCENDC_TPL_SEL 致运行时分发静默 no-op 跳过](../../../runbooks/compilation/ascendc_tpl_sel_no_op.md)（`exemplifies`）：GET_TPL_TILING_KEY 按声明位宽组合模板参数，正是本卡要求 host SetTilingKey 下发的值；其位编码契约连接 host 路由和 kernel SEL。
- [IcpuSetTilingKey](../../simd_api/basic_api/debug_interface/cpu_twin_debug/icpu_set_tiling_key.md)（`related`）：IcpuSetTilingKey 与《GET_TPL_TILING_KEY》的实质衔接是：IcpuSetTilingKey 只在 CPU 孪生调试中选择 IcpuRunKf 的 kernel 分支；TILING_KEY 宏及路由故障卡直接约束编码、缓存和 funcEntry 映射。
- [模板参数定义](template_params_definition.md)（`related`）：GET_TPL_TILING_KEY 按定义的位宽和顺序编码运行时 TilingKey，必须与模板参数定义保持一致。
- [ASCENDC_TPL_SEL_PARAM](ascendc_tpl_sel_param.md)（`same_topic`）：ASCENDC_TPL_SEL_PARAM 与《GET_TPL_TILING_KEY》的实质衔接是：TPL 参数必须与模板定义、GET_TPL_TILING_KEY 和 TILING_KEY_IS 位编码一致；所选故障卡覆盖缺宏、头文件、funcEntry 和缓存复用失配。
- [TILING_KEY_LIST](../../simd_api/basic_api/kernel_tiling/tiling_key_list.md)（`same_topic`）：GET_TPL_TILING_KEY说明Tiling模板编程时，开发者通过调用此接口自动生成TilingKey。该接口将传入的模板参数通过定义的位宽，转成二进制，按照顺序组合后转成uint64数值，即TilingKey。 使用该接口需要包含定义模板参数和模板参数组合的头文件。详细内容请参考Tiling模板编程。
- [Tiling模板编程](tiling_template_programming.md)（`same_topic`）：Tiling模板编程 与《GET_TPL_TILING_KEY》的实质衔接是：Tiling 模板编程依赖参数声明、选择宏和 key 获取；所选编译故障直接约束模板类型与分发实例化。
<!-- cannbot:related:end -->
