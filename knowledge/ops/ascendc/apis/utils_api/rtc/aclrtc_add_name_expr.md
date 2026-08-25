---
type: API
title: aclrtcAddNameExpr
description: 注册指定的名称表达式，该表达式代表了一个__global__函数。 主要用于__global__函数为模板函数的场景，调用本接口后，可以通过aclrtcGetLoweredName接口获取函数的mangling
  name，在launch阶段调用对应的模板__global__函数。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/RTC/aclrtcAddNameExpr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# aclrtcAddNameExpr

## 功能说明
注册指定的名称表达式，该表达式代表了一个__global__函数。
主要用于__global__函数为模板函数的场景，调用本接口后，可以通过aclrtcGetLoweredName接口获取函数的mangling name，在launch阶段调用对应的模板__global__函数。
## 函数原型
## 参数说明
接口参数说明
## 返回值说明
aclError为int类型变量，详细说明请参考RTC错误码。
## 约束说明
该接口需要在aclrtcCompileProg编译接口前使用。

<!-- cannbot:related:start -->
## 相关

- [编译与执行RTC](../../../guides/programming_guide/compilation_and_execution/operator_compilation/rtc_runtime_compilation.md)（`explains`）：指南把 aclrtcAddNameExpr 定位为模板核编译前的可选步骤；接口卡明确它必须在 CompileProg 前调用。
- [aclrtcCompileProg](aclrtc_compile_prog.md)（`related`）：aclrtcAddNameExpr 必须在 aclrtcCompileProg 前调用，编译完成后才能为已注册模板 kernel 解析 lowered name。
- [aclrtcCreateProg](aclrtc_create_prog.md)（`related`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《aclrtcAddNameExpr》明确提供“注册指定的名称表达式，该表达式代表了一个__global__函数。 主要用于__global__函数为模板函数的场景，调用本接口后，可以通过aclrtcGetLoweredName接口获取函数的mangling name，在launch阶段调用对应的模板__global__函数。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [aclrtcGetLoweredName](aclrtc_get_lowered_name.md)（`same_topic`）：《aclrtcGetLoweredName》处理“获取已经注册的__global__函数的mangling name。”。《aclrtcAddNameExpr》明确“注册指定的名称表达式，该表达式代表了一个__global__函数。 主要用于__global__函数为模板函数的场景，调用本接口后，可以通过aclrtcGetLoweredName接口获取函数的mangling name，在launch阶段调用对应的模板__global__函数。”，可直接用于核对RTC name expression 到 lowered symbol 的 create/compile/query/destroy 生命周期。
<!-- cannbot:related:end -->
