---
type: API
title: aclmdlFinalizeDump
description: Dump 去初始化，关闭 Dump 功能并释放相关资源。
tags:
- task.lookup
- task.debugging
- topic.implementation.debugging
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/18_dump_configuration.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
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

# aclmdlFinalizeDump

## 功能说明

Dump 去初始化，与 [aclmdlInitDump](aclmdl_init_dump.md) 配对使用。关闭 Dump 功能后需重新 init 和 set 才能再次启用。

## 函数原型

```c
aclError aclmdlFinalizeDump()
```

## 参数说明

无

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 与 [aclmdlInitDump](aclmdl_init_dump.md) 配对使用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/adump/2_model_dump_config/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/adump/2_model_dump_config/main.cpp#L79)
