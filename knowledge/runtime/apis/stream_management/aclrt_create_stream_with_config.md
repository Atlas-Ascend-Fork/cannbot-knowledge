---
type: API
title: aclrtCreateStreamWithConfig
description: 创建带优先级和 flag 的 Stream，支持快速下发/同步/持久化等模式。
tags:
- task.lookup
- topic.implementation.resource_lifecycle
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

# aclrtCreateStreamWithConfig

## 功能说明

创建带优先级和 flag 的 Stream。相比 [aclrtCreateStream](aclrt_create_stream.md)，本接口可在创建时预申请内部资源（ACL_STREAM_FAST_LAUNCH）或启用快速同步（ACL_STREAM_FAST_SYNC）。

内部行为 （固定 commit `b523035a` 源码结论）：

- 将 ACL 层 flag 映射为 RTS 层 `rtStreamCreateAttr_t`（priority / flags），通过 `rtsStreamCreate(stream, &config)` 传递。支持的 flag 映射：ACL_STREAM_FAST_LAUNCH→RT_STREAM_FAST_LAUNCH，ACL_STREAM_FAST_SYNC→RT_STREAM_FAST_SYNC，ACL_STREAM_PERSISTENT→RT_STREAM_PERSISTENT，ACL_STREAM_HUGE→RT_STREAM_HUGE，ACL_STREAM_CPU_SCHEDULE→RT_STREAM_CPU_SCHEDULE，ACL_STREAM_DEVICE_USE_ONLY→RT_STREAM_CP_PROCESS_USE。

## 函数原型

```c
aclError aclrtCreateStreamWithConfig(aclrtStream *stream, uint32_t priority, uint32_t flag)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输出 | Stream 的指针。 |
| priority | 输入 | 优先级，数字越小优先级越高。 |
| flag | 输入 | Stream flag，支持单个或多个宏按位或。详见 flag 取值说明。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- ACL_STREAM_DEVICE_USE_ONLY 仅 950、A3、A2、310p 支持。
- ACL_STREAM_HUGE 当前版本不生效。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/stream/1_stream_with_failure_mode/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/stream/1_stream_with_failure_mode/main.cpp#L83)
- [`1_basic_features/stream/3_stream_config_query/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/stream/3_stream_config_query/main.cpp#L95)
- [`2_advanced_features/label/0_simple_label/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/label/0_simple_label/main.cpp#L66)
