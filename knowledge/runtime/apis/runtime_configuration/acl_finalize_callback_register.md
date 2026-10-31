---
type: API
title: aclFinalizeCallbackRegister
description: 注册去初始化回调函数。在 aclFinalize 之前调用，去初始化时触发。
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
# aclFinalizeCallbackRegister

## 功能说明

注册去初始化回调函数。注册后在 `aclFinalizeInternal` 执行时通过 `InitCallbackManager::NotifyFinalizeCallback` 按 type 触发。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclFinalizeInternal` 中依次以 `ACL_REG_TYPE_ACL_OP_COMPILER`、`ACL_REG_TYPE_ACL_MODEL`、`ACL_REG_TYPE_ACL_DVPP`、`ACL_REG_TYPE_OTHER` 调用 `NotifyFinalizeCallback`。
- 回调通过 `InitCallbackManager` 管理，与 Init 回调池独立。

## 函数原型

```c
aclError aclFinalizeCallbackRegister(aclRegisterCallbackType type, aclFinalizeCallbackFunc cbFunc, void *userData);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| type | 输入 | 注册类型，参见 aclRegisterCallbackType。 |
| cbFunc | 输入 | 去初始化回调函数。原型：`typedef aclError (*aclFinalizeCallbackFunc)(void* userData)`。 |
| userData | 输入 | 传递给回调函数的用户数据指针。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/5_runtime_lifecycle_callbacks/0_reference_counted_plugin_lifecycle/plugin_lifecycle.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/5_runtime_lifecycle_callbacks/0_reference_counted_plugin_lifecycle/plugin_lifecycle.cpp#L117)
