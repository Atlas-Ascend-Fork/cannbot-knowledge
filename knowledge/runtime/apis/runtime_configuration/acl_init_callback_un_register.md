---
type: API
title: aclInitCallbackUnRegister
description: 取消注册初始化回调函数。已注册的回调不再触发。
tags:
- task.lookup
- topic.implementation.callback
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/02_initialization_and_deinitialization.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/acl.cpp
  role: implementation
source_headers:
- include/external/acl/acl.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclInitCallbackUnRegister

## 功能说明

若不需要触发回调函数的调用，可调用本接口取消注册初始化回调函数。

## 函数原型

```c
aclError aclInitCallbackUnRegister(aclRegisterCallbackType type, aclInitCallbackFunc cbFunc);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| type | 输入 | 注册类型，参见 aclRegisterCallbackType。 |
| cbFunc | 输入 | 初始化回调函数。原型同 `aclInitCallbackFunc`。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/5_runtime_lifecycle_callbacks/0_reference_counted_plugin_lifecycle/plugin_lifecycle.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/5_runtime_lifecycle_callbacks/0_reference_counted_plugin_lifecycle/plugin_lifecycle.cpp#L86)
