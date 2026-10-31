---
type: API
title: aclrtApiInjectionGetFunc
description: 获取指定名称的Runtime接口的原始实现函数指针和当前实现函数指针。
tags:
- task.lookup
- task.debugging
- topic.implementation.debugging
- topic.implementation.resource_query
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

# aclrtApiInjectionGetFunc

## 功能说明

获取指定名称的Runtime接口的原始实现函数指针和当前实现函数指针。
在运行时初始化阶段，原始实现指针（`originFunc`）与当前实现指针（`currentFunc`）相等。当调用[aclrtApiInjectionSetFunc](aclrt_api_injection_set_func.md)注入Hook函数后，`currentFunc`指向Hook函数，`originFunc`保持不变。当查询`originFunc`和`currentFunc`不一致时，表示该接口实现已被Hook函数替换。

## 函数原型

```c
aclError aclrtApiInjectionGetFunc(const char* name, aclrtApiFunc* originFunc, aclrtApiFunc* currentFunc)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| name | 输入 | Runtime接口名称，需与Runtime接口名称完全匹配，例如`"aclrtMemcpy"`。 |
| originFunc | 输出 | 原始函数指针。若不需要可传nullptr。类型定义请参见aclrtApiFunc。 |
| currentFunc | 输出 | 当前函数指针。若不需要可传nullptr。类型定义请参见aclrtApiFunc。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。


## 约束说明

- 对于不支持Hook功能的产品型号，本接口返回`ACL_ERROR_FEATURE_UNSUPPORTED`。
- 调用[aclrtApiInjectionSetFunc](aclrt_api_injection_set_func.md)接口和aclrtApiInjectionGetFunc接口时，需由用户保证多线程调用时序。
