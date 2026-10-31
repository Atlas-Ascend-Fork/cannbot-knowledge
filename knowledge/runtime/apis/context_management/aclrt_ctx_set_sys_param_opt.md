---
type: API
title: aclrtCtxSetSysParamOpt
description: "设置 Context 级系统参数，如确定性、调试 Kernel 和强一致性；重复设置以最后一次为准，与进程级参数区分。"
tags:
- task.lookup
- topic.implementation
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

# aclrtCtxSetSysParamOpt

## 功能说明

设置当前 Context 中的系统参数值，多次调用以最后一次设置的值为准。作用域为 Context 级别，与进程级的 [aclrtSetSysParamOpt](../runtime_configuration/aclrt_set_sys_param_opt.md) 区分。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtCtxSetSysParamOpt(opt, value)` 到 RTS 层。支持的 opt：`ACL_OPT_DETERMINISTIC`(0)、`ACL_OPT_ENABLE_DEBUG_KERNEL`(1)、`ACL_OPT_STRONG_CONSISTENCY`(2)；传入其他值返回 `ACL_ERROR_INVALID_PARAM`。

## 函数原型

```c
aclError aclrtCtxSetSysParamOpt(aclSysParamOpt opt, int64_t value)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| opt | 输入 | 系统参数类型（aclSysParamOpt）。 |
| value | 输入 | 系统参数值。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。无效 opt 返回 ACL_ERROR_INVALID_PARAM。

## 约束说明

- 仅支持 ACL_OPT_DETERMINISTIC、ACL_OPT_ENABLE_DEBUG_KERNEL、ACL_OPT_STRONG_CONSISTENCY 三种 opt。
- 不调用本接口直接调用 [aclrtCtxGetSysParamOpt](aclrt_ctx_get_sys_param_opt.md) 会失败。
- IPV350 不支持。
