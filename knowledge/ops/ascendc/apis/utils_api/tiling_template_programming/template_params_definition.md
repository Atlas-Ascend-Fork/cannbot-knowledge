---
type: API
title: 模板参数定义
description: 通过以下函数原型进行模板参数ASCENDC_TPL_ARGS_DECL和模板参数组合ASCENDC_TPL_ARGS_SEL（即可使用的模板）的定义。详细内容请参考Tiling模板编程。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_template_programming/template_params_definition.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# 模板参数定义

## 功能说明
通过以下函数原型进行模板参数ASCENDC_TPL_ARGS_DECL和模板参数组合ASCENDC_TPL_ARGS_SEL（即可使用的模板）的定义。详细内容请参考Tiling模板编程。
## 函数原型
## 参数说明
Tiling模板参数定义说明
Tiling模板参数组合定义
## 返回值说明
无。
## 约束说明
对模板参数定义的取值进行修改或新增后，需要重新编译自定义算子包，不能再继续使用之前的算子二进制。

<!-- cannbot:related:start -->
## 相关

- [GET_TPL_TILING_KEY](get_tpl_tiling_key.md)（`related`）：“使用该接口需要包含定义模板参数和模板参数组合的头文件。详细内容请参考Tiling模板编程。”与“通过以下函数原型进行模板参数ASCENDC_TPL_ARGS_DECL和模板参数组合ASCENDC_TPL_ARGS_SEL（即可使用的模板）的定义。详细内容请参考Tiling模板编程。”提供双方正文证据。GET_TPL_TILING_KEY 明确依赖模板参数和组合定义，另一卡给出 ASCENDC_TPL_ARGS_DECL/SEL 这两个定义入口，形成定义后再编码 TilingKey 的顺序。
- [ASCENDC_TPL_SEL_PARAM](ascendc_tpl_sel_param.md)（`same_topic`）：“使用前需包含定义模板参数和模板参数组合的头文件。”；“通过以下函数原型进行模板参数ASCENDC_TPL_ARGS_DECL和模板参数组合ASCENDC_TPL_ARGS_SEL（即可使用的模板）的定义。”。目标接口生产焦点宏运行前必须具备的模板参数声明与组合。
<!-- cannbot:related:end -->
