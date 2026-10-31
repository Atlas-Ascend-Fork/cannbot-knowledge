---
type: API
title: aclmdlInitDump
description: Dump 初始化，与 aclmdlSetDump/aclmdlFinalizeDump 配合使用实现算子数据 Dump 落盘或回调获取。
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

# aclmdlInitDump

## 功能说明

Dump初始化。需与 [aclmdlSetDump](aclmdl_set_dump.md)、[aclopStartDumpArgs](aclop_start_dump_args.md) 或 [acldumpRegCallback](acldump_reg_callback.md) 配合使用。调用后加载的模型受 Dump 配置影响。

必须在 [aclInit](../runtime_configuration/acl_init.md) 之后、模型加载之前调用。

## 函数原型

```c
aclError aclmdlInitDump()
```

## 参数说明

无

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 若已通过 [aclInit](../runtime_configuration/acl_init.md) 配置了 dump 信息，则调用 aclmdlInitDump 返回失败。
- 必须在 [aclInit](../runtime_configuration/acl_init.md) 之后调用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/adump/2_model_dump_config/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/adump/2_model_dump_config/main.cpp#L27)
