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

- [ACLNN 361001 — tilingKey 与 funcEntry 映射失](../../../runbooks/compilation/aclnn_361001_tilingkey_funcentry_sel_position.md)（`exemplifies`）：“宏展开后调用 GET_TPL_TILING_KEY 计算模板参数对应的 key 值，再通过 context->SetTilingKey 设置。”；“运行时**直接令 `funcEntry = tilingKey`** 查找入口。”。运行手册给出焦点宏下发 key 后与 funcEntry 映射失配导致 361001 的诊断链。
- [缺 ASCENDC_TPL_SEL 致运行时分发静默 no-op 跳过](../../../runbooks/compilation/ascendc_tpl_sel_no_op.md)（`exemplifies`）：“典型用法：在 TilingFunc 中根据数据类型、切分策略等条件确定模板参数值，调用 ASCENDC_TPL_SEL_PARAM(context, D_T_X, D_T_Y, D_T_Z, TILE_NUM, IS_SPLIT) 自动设置 TilingKey。”；“规范要求模板化入口 `template <bool templateType, bool isEmptyTensor, bool isTailR> __global__ __aicore__ void euclidean_norm(...)`，由 `ASCENDC_TPL_SEL` 在 `*_struct.h` 内声明 5 个 sub-kernel 实例、host 用 `SetTilingKey(GET_TPL_TILING_KEY(...))` 运行期选择。”。运行手册以失败实例说明焦点宏所在 Host→key→sub-kernel 链缺失会静默 no-op。
- [HardshrinkBackward 950 ACLNN 算子知识](../../../operators/aclnn/nn/activation/hardshrink_backward_950.md)（`related`）：“-> ASCENDC_TPL_SEL_PARAM(dtype, BUFFER_MODE)”展示 HardshrinkBackward Host selector 的实际调用；“宏展开后调用 GET_TPL_TILING_KEY 计算模板参数对应的 key 值，再通过 context->SetTilingKey 设置。”给出该调用如何生成 TilingKey，可直接核对 dtype 与 BUFFER_MODE 到 Device 模板的路由。
- [GET_TPL_TILING_KEY](get_tpl_tiling_key.md)（`same_topic`）：“宏展开后调用 GET_TPL_TILING_KEY 计算模板参数对应的 key 值，再通过 context->SetTilingKey 设置。”；“该接口将传入的模板参数通过定义的位宽，转成二进制，按照顺序组合后转成uint64数值，即TilingKey。”。目标接口定义焦点宏内部生成 key 的编码步骤。
- [模板参数定义](template_params_definition.md)（`same_topic`）：“使用前需包含定义模板参数和模板参数组合的头文件。”；“通过以下函数原型进行模板参数ASCENDC_TPL_ARGS_DECL和模板参数组合ASCENDC_TPL_ARGS_SEL（即可使用的模板）的定义。”。目标接口生产焦点宏运行前必须具备的模板参数声明与组合。
<!-- cannbot:related:end -->
