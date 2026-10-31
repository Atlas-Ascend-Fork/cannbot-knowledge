---
type: API
title: aclrtGetResInCurrentThread
description: 获取当前线程可使用的 Device 资源。按 Stream 限制 > 进程限制 > 硬件默认的优先级返回。
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
# aclrtGetResInCurrentThread

## 功能说明

获取当前线程可使用的 Device 资源。优先级：Stream 级别的 Device 资源限制 > 进程级别的 Device 资源限制 > AI 处理器硬件默认资源限制。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtGetResInCurrentThreadImpl`（device.cpp:492）对 value 做空指针校验，通过 `rtsGetResInCurrentThread(static_cast<rtDevResLimitType_t>(type), value)` 读取当前线程生效的资源限制。

## 函数原型

```c
aclError aclrtGetResInCurrentThread(aclrtDevResLimitType type, uint32_t *value);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| type | 输入 | 资源类型，参见 aclrtDevResLimitType。 |
| value | 输出 | 资源数量。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 | 触发点 | 调用方处理 |
| --- | --- | --- |
| `ACL_ERROR_INVALID_PARAM` | value 为空指针 | 提供有效的输出指针 |

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/context/0_context_query/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/context/0_context_query/main.cpp#L72)
