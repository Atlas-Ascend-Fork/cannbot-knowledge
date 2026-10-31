---
type: API
title: acltdtGetDataItem
description: 获取acltdtDataset中的第n个acltdtDataItem。
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
updated_at: '2026-10-30T07:10:24Z'
platforms:
- '950'
- a3
- a2
- '910'
---

# acltdtGetDataItem

## 功能说明

获取acltdtDataset中的第n个acltdtDataItem。

## 函数原型

```c
acltdtDataItem *acltdtGetDataItem(const acltdtDataset *dataset, size_t index)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| dataset | 输入 | acltdtDataset类型的指针。<br>需提前调用[acltdtCreateDataset](acltdt_create_dataset.md)接口创建acltdtDataset类型的数据，再调用[acltdtAddDataItem](acltdt_add_data_item.md)接口添加acltdtDataItem。 |
| index | 输入 | 表明获取的是第几个acltdtDataItem。 |

## 返回值说明

- 获取成功，返回acltdtDataItem的地址。
- 获取失败返回空地址。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/tdt_channel/0_simple_channel/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_channel/0_simple_channel/main.cpp#L27)
- [`2_advanced_features/tdt_channel/1_channel_capacity/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_channel/1_channel_capacity/main.cpp#L62)
- [`2_advanced_features/tdt_common_utils.h`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_common_utils.h#L62)
