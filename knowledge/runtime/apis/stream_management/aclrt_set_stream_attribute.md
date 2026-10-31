---
type: API
title: aclrtSetStreamAttribute
description: "设置已创建 Stream 的溢出检测、Launch Blocking 等属性；不同于创建前设置 StreamConfigHandle 配置。"
tags:
- task.lookup
- topic.implementation
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
updated_at: "2026-10-30T08:26:15Z"
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

# aclrtSetStreamAttribute

## 功能说明

设置 Stream 属性值，包括溢出检测属性、Launch Blocking Mode 等。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtsStreamSetAttribute(stream, stmAttrId, attrValue)` 到 RTS 层。

## 函数原型

```c
aclError aclrtSetStreamAttribute(aclrtStream stream, aclrtStreamAttr stmAttrType, aclrtStreamAttrValue *value)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 指定 Stream。 |
| stmAttrType | 输入 | 属性类型（aclrtStreamAttr）。 |
| value | 输入 | 属性值（aclrtStreamAttrValue）。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- LAUNCH_BLOCKING_MODE 属性仅 950、A3、A2 支持。
- 950、A3、A2 支持默认 Stream（stream=NULL）；910、310p、310b 不支持。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/kernel/4_launch_blocking/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/4_launch_blocking/main.cpp#L273)
