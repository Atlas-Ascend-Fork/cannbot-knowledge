---
type: API
title: acltdtCreateQueueRoute
description: "按源、目的队列 ID 创建一条路由配置对象，供加入 QueueRouteList 后绑定队列关系。"
tags:
- task.lookup
- topic.implementation.resource_lifecycle
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
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# acltdtCreateQueueRoute

## 功能说明

创建acltdtQueueRoute类型的数据，表示创建队列路由配置。

## 函数原型

```c
acltdtQueueRoute* acltdtCreateQueueRoute(uint32_t srcId, uint32_t dstId)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| srcId | 输入 | 源队列ID。 |
| dstId | 输入 | 目的队列ID。 |

## 返回值说明

- 返回acltdtQueueRoute类型的指针，表示成功。
- 返回nullptr，表示失败。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/tdt_queue/1_queue_route/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_queue/1_queue_route/main.cpp#L104)
