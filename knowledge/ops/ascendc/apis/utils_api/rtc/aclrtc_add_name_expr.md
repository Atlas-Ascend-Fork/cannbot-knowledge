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
