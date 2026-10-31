---
type: API
title: acltdtCreateDataItem
description: "创建单个 Tensor 数据项，记录数据或结束标志、Shape、元素类型、数据地址和长度，供加入 Dataset 传输。"
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

# acltdtCreateDataItem

## 功能说明

创建acltdtDataItem类型的数据，代表一个业务上的Tensor。
如需销毁acltdtDataItem类型的数据，请参见[acltdtDestroyDataItem](acltdt_destroy_data_item.md)。

## 函数原型

```c
acltdtDataItem *acltdtCreateDataItem(acltdtTensorType tdtType,
const int64_t *dims,
size_t dimNum,
aclDataType dataType,
void *data,
size_t size)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| tdtType | 输入 | tensor类型。类型定义请参见acltdtTensorType。 |
| dims | 输入 | tensor的Shape。 |
| dimNum | 输入 | tensor的Shape中的维度个数。 |
| dataType | 输入 | 正常数据里的数据类型。类型定义请参见aclDataType。 |
| data | 输入 | 数据地址指针。 |
| size | 输入 | 数据长度。 |

## 返回值说明

- 返回acltdtDataItem类型的指针，表示成功。
- 返回nullptr，表示失败。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/tdt_common_utils.h`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_common_utils.h#L33)
