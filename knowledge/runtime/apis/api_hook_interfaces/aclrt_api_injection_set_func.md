---
type: API
title: aclrtApiInjectionSetFunc
description: 将指定名称的Runtime接口指向对应的Hook函数实现。设置后，调用该Runtime接口时将跳转到Hook函数执行。
tags:
- task.lookup
- task.debugging
- topic.implementation.debugging
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/27_api_hook_interfaces.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/dfx.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-30T07:10:24Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# aclrtApiInjectionSetFunc

## 功能说明

将指定名称的Runtime接口指向对应的Hook函数实现。设置后，调用该Runtime接口时将跳转到Hook函数执行。
可通过本接口注入Hook函数，实现对Runtime接口调用的拦截和统计。若需恢复原始行为，可调用本接口并传入原始函数指针。原始函数指针可通过[aclrtApiInjectionGetFunc](aclrt_api_injection_get_func.md)获取。

## 函数原型

```c
aclError aclrtApiInjectionSetFunc(const char* name, aclrtApiFunc func)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| name | 输入 | Runtime接口名称，需与Runtime接口名称完全匹配，例如`"aclrtMemcpy"`。 |
| func | 输入 | Hook函数指针。类型定义请参见aclrtApiFunc。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。


## 约束说明

- 本接口建议在调用对应的Runtime接口之前调用，需由用户保证接口调用的时序。
- 调用aclrtApiInjectionSetFunc接口和[aclrtApiInjectionGetFunc](aclrt_api_injection_get_func.md)接口时，需由用户保证多线程调用时序。
- 当前支持Hook的接口范围为aclrt接口和aclmdlRI开头的接口，不支持[aclInit](../runtime_configuration/acl_init.md)、[aclFinalize](../runtime_configuration/acl_finalize.md)等接口。
- 对于不支持Hook功能的产品型号，本接口返回`ACL_ERROR_FEATURE_UNSUPPORTED`。
