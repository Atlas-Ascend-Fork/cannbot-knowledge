---
type: API
title: aclrtGetFunctionAttribute
description: 根据核函数句柄获取核函数属性信息。仅支持查询算子二进制中的核函数属性。
tags:
- task.lookup
- topic.implementation.kernel_launch
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/14_Kernel_loading_and_execution.md
    role: primary
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
    role: header
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/kernel.cpp
    role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
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

# aclrtGetFunctionAttribute

## 功能说明

根据核函数句柄获取核函数属性信息。仅支持查询算子二进制中的核函数属性。

## 函数原型

```c
aclError aclrtGetFunctionAttribute(aclrtFuncHandle funcHandle, aclrtFuncAttribute attrType, int64_t *attrValue)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| funcHandle | 输入 | 核函数句柄。 |
| attrType | 输入 | 属性类型：aclrtFuncAttribute。 |
| attrValue | 输出 | 属性值。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

委托 `rtFunctionGetAttribute(funcHandle, static_cast<rtFuncAttribute>(attrType), attrValue)` 到 RTS 层。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/kernel/5_fdtd_stencil/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/5_fdtd_stencil/main.cpp#L46)
