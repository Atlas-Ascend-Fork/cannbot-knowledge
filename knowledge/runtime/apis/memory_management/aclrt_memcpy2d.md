---
type: API
title: aclrtMemcpy2d
description: "按源、目的 pitch 同步复制 width×height 的二维矩阵区域；当前仅支持 Host 与 Device 间双向复制。"
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
# aclrtMemcpy2d

## 功能说明

实现二维同步内存复制，主要用于矩阵数据。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- aclrtMemcpy2dImpl 校验参数后调用 rtMemcpy2d。

## 函数原型

```c
aclError aclrtMemcpy2d(void *dst, size_t dpitch, const void *src, size_t spitch, size_t width, size_t height, aclrtMemcpyKind kind)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| dst | 输入 | 目的内存地址指针 |
| dpitch | 输入 | 目的内存中相邻两列向量的地址距离 |
| src | 输入 | 源内存地址指针 |
| spitch | 输入 | 源内存中相邻两列向量的地址距离 |
| width | 输入 | 待复制的数据宽度 |
| height | 输入 | 待复制的数据高度 |
| kind | 输入 | 内存复制类型 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 当前仅支持 HOST_TO_DEVICE 和 DEVICE_TO_HOST

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`6_scenarios/image_processing/1_pitched_image_shift/pitched_image_shift.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/6_scenarios/image_processing/1_pitched_image_shift/pitched_image_shift.cpp#L120)
