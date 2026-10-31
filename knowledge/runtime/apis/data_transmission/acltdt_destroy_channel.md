---
type: API
title: acltdtDestroyChannel
description: "销毁 CreateChannel 或 CreateChannelWithCapacity 创建的数据通道，输入通道句柄而非队列 ID。"
tags:
- task.lookup
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/17-01_tensor_data_transfer.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_tdt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/acl_tdt_channel/tensor_data_transfer.cpp
  role: implementation
source_headers:
- include/external/acl/acl_tdt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- a3
- a2
- '910'
---
# acltdtDestroyChannel

## 功能说明

销毁通道。

## 函数原型

```c
aclError acltdtDestroyChannel(acltdtChannelHandle *handle)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| handle | 输入 | 待销毁的通道指针。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

只能销毁通过 CreateChannel 或 CreateChannelWithCapacity 创建的通道。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/tdt_channel/0_simple_channel/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_channel/0_simple_channel/main.cpp#L110)
- [`2_advanced_features/tdt_channel/1_channel_capacity/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_channel/1_channel_capacity/main.cpp#L117)
