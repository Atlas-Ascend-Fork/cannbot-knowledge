---
type: API
title: acltdtGetTensorTypeFromItem
description: "判断收到的 DataItem 是正常数据、结束标记还是异常数据，返回 acltdtTensorType，供决定后续处理方式。"
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/25-03_Operation_APIs.md
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

# acltdtGetTensorTypeFromItem

## 功能说明

收到dataItem数据之后，从数据描述里首先check这个数据是个正常数据，还是一个end数据，还是一个异常数据。

## 函数原型

```c
acltdtTensorType acltdtGetTensorTypeFromItem(const acltdtDataItem *dataItem)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| dataItem | 输入 | acltdtDataItem类型的指针。<br>需提前调用[acltdtCreateDataItem](acltdt_create_data_item.md)接口创建acltdtDataItem类型的数据。 |

## 返回值说明

请参见acltdtTensorType。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/tdt_channel/0_simple_channel/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_channel/0_simple_channel/main.cpp#L42)
- [`2_advanced_features/tdt_channel/1_channel_capacity/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_channel/1_channel_capacity/main.cpp#L73)
