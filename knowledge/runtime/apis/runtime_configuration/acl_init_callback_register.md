---
type: API
title: aclInitCallbackRegister
description: 注册初始化回调函数。在 aclInit 之前调用则在初始化时触发，在 aclInit 之后调用则立即触发。
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
# aclInitCallbackRegister

## 功能说明

注册初始化回调函数。注册的回调通过 `InitCallbackManager` 在 [aclInit](acl_init.md) 阶段（或注册时立即）触发。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclInitImpl` 在不同阶段依次调用 `InitCallbackManager::NotifyInitCallback` 触发各注册类型的回调（如 ACL_REG_TYPE_ACL_MODEL、ACL_REG_TYPE_ACL_OP_EXECUTOR 等）。本接口即向该管理器注册回调。
- 若在 [aclInit](acl_init.md) 前调用，回调被记录，在 `NotifyInitCallback` 时按 type 依序执行。
- 若在 [aclInit](acl_init.md) 后调用，注册时立即执行；执行失败时返回对应的 aclError。

## 函数原型

```c
aclError aclInitCallbackRegister(aclRegisterCallbackType type, aclInitCallbackFunc cbFunc, void *userData);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| type | 输入 | 注册类型，参见 aclRegisterCallbackType。 |
| cbFunc | 输入 | 初始化回调函数。原型：`typedef aclError (*aclInitCallbackFunc)(const char* configStr, size_t len, void *userData)`。 |
| userData | 输入 | 传递给回调函数的用户数据指针。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 回调函数中的 configStr 与 [aclInit](acl_init.md) 的 json 文件内容保持一致。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/5_runtime_lifecycle_callbacks/0_reference_counted_plugin_lifecycle/plugin_lifecycle.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/5_runtime_lifecycle_callbacks/0_reference_counted_plugin_lifecycle/plugin_lifecycle.cpp#L82)
