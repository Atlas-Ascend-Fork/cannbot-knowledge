---
type: API
title: acltdtGetDataSizeFromItem
description: "从单个 DataItem 读取正常 Tensor 数据的长度，与 GetDatasetSize 返回的数据项数量区分。"
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

# acltdtGetDataSizeFromItem

## 功能说明

得到正常数据的数据长度。

## 函数原型

```c
size_t acltdtGetDataSizeFromItem(const acltdtDataItem *dataItem)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| dataItem | 输入 | acltdtDataItem类型的指针。<br>需提前调用[acltdtCreateDataItem](acltdt_create_data_item.md)接口创建acltdtDataItem类型的数据。 |

## 返回值说明

获取到的数据长度。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/tdt_channel/0_simple_channel/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_channel/0_simple_channel/main.cpp#L43)
