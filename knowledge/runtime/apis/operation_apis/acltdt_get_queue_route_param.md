---
type: API
title: acltdtGetQueueRouteParam
description: 获取队列路由配置的相关信息，例如源队列ID、目标队列ID等。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/25-03_Operation_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_tdt_queue.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/acl_tdt_queue/queue.cpp
  role: implementation
source_headers:
- include/external/acl/acl_tdt_queue.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-30T07:10:24Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# acltdtGetQueueRouteParam

## 功能说明

获取队列路由配置的相关信息，例如源队列ID、目标队列ID等。

## 函数原型

```c
aclError acltdtGetQueueRouteParam(const acltdtQueueRoute *route, acltdtQueueRouteParamType type, size_t len, size_t *paramRetSize, void *param)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| route | 输入 | 队列路由配置信息的指针。<br>需提前调用[acltdtCreateQueueRoute](acltdt_create_queue_route.md)接口创建acltdtQueueRoute类型的数据。 |
| type | 输入 | 路由参数类型。类型定义请参见acltdtQueueRouteParamType。 |
| len | 输入 | 参数值的字节数。<br>type取值的枚举名以_UINT32或_INT32结尾，此处固定配置为4。 |
| paramRetSize | 输出 | 实际返回的参数值字节数的指针。 |
| param | 输出 | 指向参数值的指针。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/tdt_queue/1_queue_route/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_queue/1_queue_route/main.cpp#L148)
