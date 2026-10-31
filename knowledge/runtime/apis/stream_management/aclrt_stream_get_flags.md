---
type: API
title: aclrtStreamGetFlags
description: 查询创建 Stream 时设置的 flag。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/06_stream_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/stream.cpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/api_c_stream.cc
  role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtStreamGetFlags

## 功能说明

查询创建 Stream 时设置的 flag 标志。传入 NULL 获取默认 Stream 的 flag。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtStreamGetFlags(stream, &rtFlags)` 到 RTS 层；ACL 层将 RTS 返回的 flag 反向映射为 ACL 层宏值。

## 函数原型

```c
aclError aclrtStreamGetFlags(aclrtStream stream, uint32_t *flags)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 指定 Stream。传入 NULL 获取默认 Stream flag。 |
| flags | 输出 | flag 值，多个 flag 按位或的结果。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 默认 Stream 的 flag 因产品型号而异，应以本接口查询为准。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/stream/3_stream_config_query/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/stream/3_stream_config_query/main.cpp#L72)
- [`6_scenarios/image_processing/0_watershed_image_staging/watershed_image_staging.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/6_scenarios/image_processing/0_watershed_image_staging/watershed_image_staging.cpp#L80)
