---
type: API
title: aclrtGetStreamOverflowSwitch
description: 获取指定 Stream 的溢出检测开关状态。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.precision
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
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtGetStreamOverflowSwitch

## 功能说明

获取指定 Stream 的当前溢出检测开关是否打开。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtGetStreamOverflowSwitch(stream, flag)` 到 RTS 层。

## 函数原型

```c
aclError aclrtGetStreamOverflowSwitch(aclrtStream stream, uint32_t *flag)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 待操作 Stream。 |
| flag | 输出 | 溢出检测开关：0=关闭，1=打开。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 仅 950、A3、A2 支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`4_reliability/overflow_detection/0_overflow_detection/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/4_reliability/overflow_detection/0_overflow_detection/main.cpp#L127)
