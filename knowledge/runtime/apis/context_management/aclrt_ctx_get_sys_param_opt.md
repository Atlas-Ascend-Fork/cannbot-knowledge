---
type: API
title: aclrtCtxGetSysParamOpt
description: "查询当前 Context 的系统参数；无默认值，须先调用 aclrtCtxSetSysParamOpt，未设置时返回错误。"
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/05_context_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/context.cpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/api_c_context.cc
  role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtCtxGetSysParamOpt

## 功能说明

获取当前 Context 中的系统参数值。系统参数无默认值，必须先设置再获取。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtCtxGetSysParamOpt(opt, value)` 到 RTS 层。若参数未设置，RTS 返回 `RT_ERROR_NOT_SET_SYSPARAMOPT`（RTS 层映射为 `ACL_ERROR_RT_SYSPARAMOPT_NOT_SET`），ACL 层记 WARN 日志。

## 函数原型

```c
aclError aclrtCtxGetSysParamOpt(aclSysParamOpt opt, int64_t *value)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| opt | 输入 | 系统参数类型（aclSysParamOpt）。 |
| value | 输出 | 存放系统参数值的指针。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。opt 未设置时返回对应错误码。

## 约束说明

- 需先调用 [aclrtCtxSetSysParamOpt](aclrt_ctx_set_sys_param_opt.md) 设置后方可获取。
- IPV350 不支持。
