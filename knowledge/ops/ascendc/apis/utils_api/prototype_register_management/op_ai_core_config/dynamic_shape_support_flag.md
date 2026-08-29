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

- [bisheng 动态 shape 编译段错误 — extern C + DTYPE](../../../../runbooks/compilation/bisheng_extern_c_dtype_dynamic_shape_segfault.md)（`exemplifies`）：算子 def.cpp 设 `DynamicRankSupportFlag(true)` + `DynamicShapeSupportFlag(true)`，kernel 入口为 `extern "C"`（非 template），kernel 内用 `DTYPE_*` 宏区分 dtype；GEIR 用动态 shape（`-1`/`-2`）调 `RunGraph` 触发 TBE 重编译。；用于标识该算子是否支持入图时的动态Shape场景。。运行手册以 DynamicShapeSupportFlag 开启后的动态 shape TBE 重编译崩溃为实例，接口卡界定该标志声明的入图能力。
<!-- cannbot:related:end -->
