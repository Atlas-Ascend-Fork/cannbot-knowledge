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

- [编译与执行RTC](../../../guides/programming_guide/compilation_and_execution/operator_compilation/rtc_runtime_compilation.md)（`explains`）：“aclrtcAddNameExpr（可选）：注册需要导出的核函数名表达式”描述可选导出步骤，“该接口需要在aclrtcCompileProg编译接口前使用”给出必须满足的调用顺序。
- [aclrtcGetLoweredName](aclrtc_get_lowered_name.md)（`related`）：“使用前必须先通过aclrtcAddNameExpr注册原始名称，且两次传入的nameExpression字符串必须完全相同。”与“主要用于__global__函数为模板函数的场景，调用本接口后，可以通过aclrtcGetLoweredName接口获取函数的mangling name，在launch阶段调用对应的模板__global__函数。”分别给出双端正文事实；GetLoweredName 的前置条件是 AddNameExpr 注册完全相同的表达式，AddNameExpr 卡又明确后续由 GetLoweredName 取得 mangling name，二者形成 RTC 模板函数注册到 launch 名称查询的调用序。
- [aclrtcCompileProg](aclrtc_compile_prog.md)（`same_topic`）：该接口需要在aclrtcCompileProg编译接口前使用。编译接口，编译指定的程序。函数签名为 aclError aclrtcCompileProg(aclrtcProg prog, int numOptions, const char** options)。名称表达式卡规定注册时序，编译卡给出消耗同一 `aclrtcProg` 句柄的编译入口；模板 `__global__` 函数若需 lowered name，必须先注册表达式再执行编译。
<!-- cannbot:related:end -->
