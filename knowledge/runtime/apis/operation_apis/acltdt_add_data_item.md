---
type: API
title: acltdtAddDataItem
description: "把已创建的单个 Tensor 数据项加入 Dataset 容器，Dataset 和 DataItem 均须先分别创建。"
tags:
- task.lookup
- topic.implementation.resource_lifecycle
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

# acltdtAddDataItem

## 功能说明

向acltdtDataset中增加acltdtDataItem。

## 函数原型

```c
aclError acltdtAddDataItem(acltdtDataset *dataset, acltdtDataItem *dataItem)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| dataset | 输出 | 待增加acltdtDataItem的acltdtDataset地址指针。<br>需提前调用[acltdtCreateDataset](acltdt_create_dataset.md)接口创建acltdtDataset类型的数据。 |
| dataItem | 输入 | 待增加的acltdtDataItem地址指针。<br>需提前调用[acltdtCreateDataItem](acltdt_create_data_item.md)接口创建acltdtDataItem类型的数据。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/tdt_common_utils.h`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_common_utils.h#L46)
