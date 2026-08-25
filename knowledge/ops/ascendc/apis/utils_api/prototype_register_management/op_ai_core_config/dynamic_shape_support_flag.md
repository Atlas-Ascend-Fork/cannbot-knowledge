---
type: API
title: DynamicShapeSupportFlag
description: 用于标识该算子是否支持入图时的动态Shape场景。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICoreConfig/DynamicShapeSupportFlag.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# DynamicShapeSupportFlag

## 功能说明
用于标识该算子是否支持入图时的动态Shape场景。
## 函数原型
## 参数说明
## 返回值说明
OpAICoreConfig类，请参考OpAICoreConfig。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [bisheng 动态 shape 编译段错误 — extern C + DTYPE](../../../../runbooks/compilation/bisheng_extern_c_dtype_dynamic_shape_segfault.md)（`exemplifies`）：bisheng 动态 shape 编译段错误 — extern C + DTYPE 与《DynamicShapeSupportFlag》的实质衔接是：该动态 shape 崩溃与 extern C+DTYPE、动态声明和 TPL 选择形态直接相关，所选卡覆盖符号、flag 与模板入口对照。
- [DynamicCompileStaticFlag](dynamic_compile_static_flag.md)（`same_topic`）：两张卡分别声明静态形状动态编译和动态形状支持能力，是 OpAICoreConfig 上同一 shape/compile 能力决策的互补标志。
- [DynamicRankSupportFlag](dynamic_rank_support_flag.md)（`same_topic`）：《DynamicRankSupportFlag》处理“标识算子是否支持dynamicRank（动态维度）。”。《DynamicShapeSupportFlag》提供“用于标识该算子是否支持入图时的动态Shape场景。”，其具体合同或探针直接接入DynamicRank 与 DynamicShape 配置及差异化原型注册入口。
<!-- cannbot:related:end -->
