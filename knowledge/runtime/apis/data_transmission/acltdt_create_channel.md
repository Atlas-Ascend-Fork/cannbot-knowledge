---
type: API
title: acltdtCreateChannel
description: "按 Device ID 和名称创建数据通道，仅用于训练系列昇腾虚拟化实例；用完须先 StopChannel 再销毁。"
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
- '910'
---
# acltdtCreateChannel

## 功能说明

创建数据通道。

## 函数原型

```c
acltdtChannelHandle *acltdtCreateChannel(uint32_t deviceId, const char *name)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| deviceId | 输入 | Device ID。 |
| name | 输入 | 队列通道名称。 |

## 返回值说明

返回 acltdtChannelHandle 指针；失败返回 nullptr。

## 约束说明

仅 Atlas 训练系列产品（昇腾虚拟化实例）。用完需 StopChannel 再 DestroyChannel。
