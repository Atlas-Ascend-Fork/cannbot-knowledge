---
type: API
title: acltdtCreateDataset
description: "创建容纳多个 Tensor DataItem 的 Dataset，配合 AddDataItem 组装通道传输数据，使用后 DestroyDataset。"
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

# acltdtCreateDataset

## 功能说明

创建acltdtDataset类型的数据，对等一个Vector<tensor\>。
如需销毁acltdtDataset类型的数据，请参见[acltdtDestroyDataset](acltdt_destroy_dataset.md)。

## 函数原型

```c
acltdtDataset *acltdtCreateDataset()
```

## 参数说明

无

## 返回值说明

- 返回acltdtDataset类型的指针，表示成功。
- 返回nullptr，表示失败。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/tdt_channel/0_simple_channel/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_channel/0_simple_channel/main.cpp#L80)
- [`2_advanced_features/tdt_common_utils.h`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_common_utils.h#L40)
