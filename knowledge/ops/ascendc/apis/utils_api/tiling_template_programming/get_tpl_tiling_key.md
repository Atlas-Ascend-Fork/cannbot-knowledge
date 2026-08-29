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

- [sub-kernel 后缀 _N 是 tilingKey 位编码非序号](../../../runbooks/compilation/sub_kernel_n_tilingkey.md)（`exemplifies`）：**API 路径**: `GET_TPL_TILING_KEY(...)` 宏 → `AscendC::FastEncodeTilingKeyDirect(g_tilingDeclareParams, {...})`（`tiling/template_argument.h:291-325`）；Tiling模板编程时，开发者通过调用此接口自动生成TilingKey。该接口将传入的模板参数通过定义的位宽，转成二进制，按照顺序组合后转成uint64数值，即TilingKey。。该 runbook 通过 sub-kernel 后缀实证 GET_TPL_TILING_KEY 的位宽顺序编码结果，说明后缀是编码值而非连续序号。
- [tilingKey 编码与 TPL 位打包不一致致路由错误](../../../runbooks/compilation/tiling_key_tpl_bit_encoding_mismatch.md)（`exemplifies`）：焦点 runbook 的修复结论是“host tilingKey 必须等于 TPL 位编码值”，候选 API 定义“该接口将传入的模板参数通过定义的位宽，转成二进制，按照顺序组合后转成uint64数值，即TilingKey。”；API 的位宽顺序正是重算 Host key、避免路由错模板的权威合同。
- [模板参数定义](template_params_definition.md)（`related`）：“使用该接口需要包含定义模板参数和模板参数组合的头文件。详细内容请参考Tiling模板编程。”与“通过以下函数原型进行模板参数ASCENDC_TPL_ARGS_DECL和模板参数组合ASCENDC_TPL_ARGS_SEL（即可使用的模板）的定义。详细内容请参考Tiling模板编程。”提供双方正文证据。GET_TPL_TILING_KEY 明确依赖模板参数和组合定义，另一卡给出 ASCENDC_TPL_ARGS_DECL/SEL 这两个定义入口，形成定义后再编码 TilingKey 的顺序。
- [ASCENDC_TPL_SEL_PARAM](ascendc_tpl_sel_param.md)（`same_topic`）：“宏展开后调用 GET_TPL_TILING_KEY 计算模板参数对应的 key 值，再通过 context->SetTilingKey 设置。”；“该接口将传入的模板参数通过定义的位宽，转成二进制，按照顺序组合后转成uint64数值，即TilingKey。”。目标接口定义焦点宏内部生成 key 的编码步骤。
<!-- cannbot:related:end -->
