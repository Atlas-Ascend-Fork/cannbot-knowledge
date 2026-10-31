---
type: API
title: aclrtGetStreamResLimit
description: 获取指定 Stream 的 Device 资源限制。未设置时优先返回进程级限制，其次返回硬件默认限制。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/03_runtime_configuration.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/device.cpp
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
# aclrtGetStreamResLimit

## 功能说明

获取指定 Stream 的 Device 资源限制。若未调用 `aclrtSetStreamResLimit` 设置，则获取到的优先级为：进程级限制 > AI 处理器硬件默认。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtGetStreamResLimitImpl`（device.cpp:437）对 value 做空指针校验，通过 `rtsGetStreamResLimit(static_cast<rtStream_t>(stream), static_cast<rtDevResLimitType_t>(type), value)` 读取。

## 函数原型

```c
aclError aclrtGetStreamResLimit(aclrtStream stream, aclrtDevResLimitType type, uint32_t *value);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 指定 Stream。传入 NULL 表示默认 Stream。 |
| type | 输入 | 资源类型，参见 aclrtDevResLimitType。 |
| value | 输出 | 资源限制的大小。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 | 触发点 | 调用方处理 |
| --- | --- | --- |
| `ACL_ERROR_INVALID_PARAM` | value 为空指针 | 提供有效的输出指针 |
| `ACL_GET_ERRCODE_RTS(rtErr)` | RTS 层查询失败 | 检查 stream 合法性 |

## 约束说明

- 应在 [aclrtSetDevice](../device_management/aclrt_set_device.md) 之后调用。