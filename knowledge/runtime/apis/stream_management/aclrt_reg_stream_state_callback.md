---
type: API
title: aclrtRegStreamStateCallback
description: "按唯一名称注册 Stream 创建、销毁等状态回调，覆盖显式流和默认流；传 NULL 回调取消注册，不允许同名重复注册。"
tags:
- task.lookup
- topic.implementation.callback
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/06_stream_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/stream.cpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/api_c_stream.cc
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

# aclrtRegStreamStateCallback

## 功能说明

注册 Stream 状态回调函数，不支持重复注册。当 Stream 状态变化时（Create/Destroy 等），Runtime 触发该回调。包含显式创建的 Stream 和默认 Stream。

## 函数原型

```c
aclError aclrtRegStreamStateCallback(const char *regName, aclrtStreamStateCallback callback, void *args)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| regName | 输入 | 注册唯一名称，不能为空，以 \0 结尾。 |
| callback | 输入 | 回调函数指针；NULL 表示取消注册。 |
| args | 输入 | 传递给回调函数的用户数据指针。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 不支持重复注册同名回调。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/stream/1_stream_with_failure_mode/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/stream/1_stream_with_failure_mode/main.cpp#L149)
