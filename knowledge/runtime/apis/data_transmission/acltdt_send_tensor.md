---
type: API
title: acltdtSendTensor
description: "通过已创建通道将 Host 的 Dataset 发送到 Device；timeout=-1 阻塞、0 非阻塞，正值指定毫秒超时。"
tags:
- task.lookup
- topic.data_movement
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
# acltdtSendTensor

## 功能说明

从 Host 向 Device 发送数据。

## 函数原型

```c
aclError acltdtSendTensor(const acltdtChannelHandle *handle, const acltdtDataset *dataset, int32_t timeout)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| handle | 输入 | 通道。需提前创建。 |
| dataset | 输入 | 数据指针。 |
| timeout | 输入 | -1 阻塞，0 非阻塞，>0 毫秒。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/tdt_channel/0_simple_channel/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_channel/0_simple_channel/main.cpp#L89)
- [`2_advanced_features/tdt_channel/1_channel_capacity/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_channel/1_channel_capacity/main.cpp#L76)
