---
type: API
title: aclrtMemcpy2dAsync
description: "在指定 Stream 上按源、目的 pitch 复制二维矩阵区域；支持 Host/Device 互拷，Device 间复制受产品型号限制。"
tags:
- task.lookup
- topic.data_movement.data_copy
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-03_memory_copy_and_set.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/memory.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtMemcpy2dAsync

## 功能说明

实现二维异步内存复制，主要用于矩阵数据。

## 函数原型

```c
aclError aclrtMemcpy2dAsync(void *dst, size_t dpitch, const void *src, size_t spitch, size_t width, size_t height, aclrtMemcpyKind kind, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| dst | 输入 | 目的内存地址指针 |
| dpitch | 输入 | 目的内存中相邻两列向量的地址距离 |
| src | 输入 | 源内存地址指针 |
| spitch | 输入 | 源内存中相邻两列向量的地址距离 |
| width | 输入 | 待复制的数据宽度，最大 5000000 |
| height | 输入 | 待复制的数据高度，最大 5242880 |
| kind | 输入 | 内存复制类型 |
| stream | 输入 | 指定执行任务的 Stream |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 仅支持 HOST_TO_DEVICE / DEVICE_TO_HOST / DEVICE_TO_DEVICE（部分型号）

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`6_scenarios/image_processing/0_watershed_image_staging/watershed_image_staging.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/6_scenarios/image_processing/0_watershed_image_staging/watershed_image_staging.cpp#L150)
