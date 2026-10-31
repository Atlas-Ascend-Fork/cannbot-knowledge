---
type: API
title: aclrtGetMemInfo
description: 根据指定属性查询 Device 上可用内存的空闲大小和总大小。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.memory
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-01_device_memory_malloc_and_free.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/memory.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtGetMemInfo

## 功能说明

根据指定属性查询 Device 上可用内存的空闲大小和总大小。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- aclrtGetMemInfoImpl 调用 rtMemGetInfo 获取指定属性的内存统计。

## 函数原型

```c
aclError aclrtGetMemInfo(aclrtMemAttr attr, size_t *free, size_t *total)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| attr | 输入 | 需查询的内存属性，见 aclrtMemAttr |
| free | 输出 | 空闲内存大小指针，单位 Byte |
| total | 输出 | 总内存大小指针，单位 Byte |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 调用前必须已指定用于计算的 Device
- 不支持 HBM 的硬件自动降级查询 DDR 信息

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`6_scenarios/image_processing/0_segmentation_tree/segmentation_tree.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/6_scenarios/image_processing/0_segmentation_tree/segmentation_tree.cpp#L60)
