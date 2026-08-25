---
type: API
title: aclrtcGetLoweredName
description: 获取已经注册的__global__函数的mangling name。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/RTC/aclrtcGetLoweredName.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# aclrtcGetLoweredName

## 功能说明
获取已经注册的__global__函数的mangling name。
## 函数原型
## 参数说明
接口参数说明
## 返回值说明
aclError为int类型变量，详细说明请参考RTC错误码。
## 约束说明
使用前必须先通过aclrtcAddNameExpr注册原始名称，且两次传入的nameExpression字符串必须完全相同。
