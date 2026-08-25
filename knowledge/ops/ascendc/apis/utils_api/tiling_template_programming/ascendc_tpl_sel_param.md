---
type: API
title: ASCENDC_TPL_SEL_PARAM
description: Tiling模板编程时，开发者通过调用此接口自动生成并配置TilingKey。 使用该接口需要包含定义模板参数和模板参数组合的头文件。详细内容请参考Tiling模板编程。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_template_programming/ASCENDC_TPL_SEL_PARAM.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# ASCENDC_TPL_SEL_PARAM

Tiling 模板编程时，开发者通过调用此宏自动生成并配置 TilingKey。使用前需包含定义模板参数和模板参数组合的头文件。
宏展开后调用 GET_TPL_TILING_KEY 计算模板参数对应的 key 值，再通过 context->SetTilingKey 设置。
参数 context 为 TilingFunc 注册上下文（gert::TilingContext*），可变参数为模板参数具体值，需与头文件中模板参数顺序一致。
无返回值，无特殊约束。
典型用法：在 TilingFunc 中根据数据类型、切分策略等条件确定模板参数值，调用 ASCENDC_TPL_SEL_PARAM(context, D_T_X, D_T_Y, D_T_Z, TILE_NUM, IS_SPLIT) 自动设置 TilingKey。

<!-- cannbot:related:start -->
## 相关

- [561103: isGroup=-1 哨兵致 tilingKey 路由失配](../../../runbooks/compilation/561103_isgroup_1_tilingkey.md)（`exemplifies`）：561103: isGroup=-1 哨兵致 tilingKey 路由失配 与《ASCENDC_TPL_SEL_PARAM》的实质衔接是：该故障是 host tiling 上下文哨兵未覆盖，使 TilingKey 路由返回 -1；key 注册/判定/获取宏和位编码案例直接用于修复并与 361001 分派缺失区分。
- [ACLNN 361001 — tilingKey 与 funcEntry 映射失](../../../runbooks/compilation/aclnn_361001_tilingkey_funcentry_sel_position.md)（`exemplifies`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《ASCENDC_TPL_SEL_PARAM》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [TilingKey 缓存 correction 致 tilingdata 复用](../../../runbooks/compilation/ge_tilingkey_cache_reuse_per_call_attr_pollution.md)（`exemplifies`）：ASCENDC_TPL_SEL_PARAM 与《TilingKey 缓存 correction 致 tilingdata 复用》的实质衔接是：TPL 参数必须与模板定义、GET_TPL_TILING_KEY 和 TILING_KEY_IS 位编码一致；所选故障卡覆盖缺宏、头文件、funcEntry 和缓存复用失配。
- [bisheng 动态 shape 编译段错误 — extern C + DTYPE](../../../runbooks/compilation/bisheng_extern_c_dtype_dynamic_shape_segfault.md)（`exemplifies`）：bisheng 动态 shape 编译段错误 — extern C + DTYPE 与《ASCENDC_TPL_SEL_PARAM》的实质衔接是：该动态 shape 崩溃与 extern C+DTYPE、动态声明和 TPL 选择形态直接相关，所选卡覆盖符号、flag 与模板入口对照。
- [kernel.h 须 include struct.h 才能识别 TPL](../../../runbooks/compilation/ascendc_tpl_kernel_h_must_include_struct_h.md)（`exemplifies`）：ASCENDC_TPL_SEL_PARAM 与《kernel.h 须 include struct.h 才能识别 TPL》的实质衔接是：TPL 参数必须与模板定义、GET_TPL_TILING_KEY 和 TILING_KEY_IS 位编码一致；所选故障卡覆盖缺宏、头文件、funcEntry 和缓存复用失配。
- [sub-kernel 后缀 _N 是 tilingKey 位编码非序号](../../../runbooks/compilation/sub_kernel_n_tilingkey.md)（`exemplifies`）：ASCENDC_TPL_SEL_PARAM 与《sub-kernel 后缀 _N 是 tilingKey 位编码非序号》的实质衔接是：TPL 参数必须与模板定义、GET_TPL_TILING_KEY 和 TILING_KEY_IS 位编码一致；所选故障卡覆盖缺宏、头文件、funcEntry 和缓存复用失配。
- [tilingKey 编码与 TPL 位打包不一致致路由错误](../../../runbooks/compilation/tiling_key_tpl_bit_encoding_mismatch.md)（`exemplifies`）：ASCENDC_TPL_SEL_PARAM 与《tilingKey 编码与 TPL 位打包不一致致路由错误》的实质衔接是：TPL 参数必须与模板定义、GET_TPL_TILING_KEY 和 TILING_KEY_IS 位编码一致；所选故障卡覆盖缺宏、头文件、funcEntry 和缓存复用失配。
- [缺 ASCENDC_TPL_SEL 致运行时分发静默 no-op 跳过](../../../runbooks/compilation/ascendc_tpl_sel_no_op.md)（`exemplifies`）：ASCENDC_TPL_SEL_PARAM 与《缺 ASCENDC_TPL_SEL 致运行时分发静默 no-op 跳过》的实质衔接是：TPL 参数必须与模板定义、GET_TPL_TILING_KEY 和 TILING_KEY_IS 位编码一致；所选故障卡覆盖缺宏、头文件、funcEntry 和缓存复用失配。
- [TILING_KEY_IS](../../simd_api/basic_api/kernel_tiling/tiling_key_is.md)（`related`）：ASCENDC_TPL_SEL_PARAM 与《TILING_KEY_IS》的实质衔接是：TPL 参数必须与模板定义、GET_TPL_TILING_KEY 和 TILING_KEY_IS 位编码一致；所选故障卡覆盖缺宏、头文件、funcEntry 和缓存复用失配。
- [模板参数定义](template_params_definition.md)（`related`）：ASCENDC_TPL_SEL_PARAM 消费已定义的模板参数及组合来生成编译实例，是参数定义后的直接下一步。
- [GET_TPL_TILING_KEY](get_tpl_tiling_key.md)（`same_topic`）：ASCENDC_TPL_SEL_PARAM 与《GET_TPL_TILING_KEY》的实质衔接是：TPL 参数必须与模板定义、GET_TPL_TILING_KEY 和 TILING_KEY_IS 位编码一致；所选故障卡覆盖缺宏、头文件、funcEntry 和缓存复用失配。
- [Tiling模板编程](tiling_template_programming.md)（`same_topic`）：ASCENDC_TPL_SEL_PARAM 与《Tiling模板编程》的实质衔接是：TPL 参数必须与模板定义、GET_TPL_TILING_KEY 和 TILING_KEY_IS 位编码一致；所选故障卡覆盖缺宏、头文件、funcEntry 和缓存复用失配。
<!-- cannbot:related:end -->
