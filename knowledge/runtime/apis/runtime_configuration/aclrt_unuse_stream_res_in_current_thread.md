---
type: API
title: aclrtUnuseStreamResInCurrentThread
description: 在当前线程中取消使用指定 Stream 上的 Device 资源限制。
tags:
- task.lookup
- topic.implementation
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/03_runtime_configuration.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/device.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
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
# aclrtUnuseStreamResInCurrentThread

## 功能说明

在当前线程中取消使用指定 Stream 上的 Device 资源限制。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtUnuseStreamResInCurrentThreadImpl`（device.cpp:482）通过 `rtsNotUseStreamResInCurrentThread(static_cast<rtStream_t>(stream))` 解除当前线程的 Stream 级限制绑定。

## 函数原型

```c
aclError aclrtUnuseStreamResInCurrentThread(aclrtStream stream);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 指定 Stream。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。