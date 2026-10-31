---
type: API
title: acltdtQueryQueueRoutes
description: "按 QueueRouteQueryInfo 条件查询路由关系，写入调用方创建的 QueueRouteList，供查看或解绑使用。"
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/17-02_shared_queue_management.md
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
- a3
- a2
- '310b'
- '310p'
- '910'
---
# acltdtQueryQueueRoutes

## 功能说明

查询队列路由关系。

## 函数原型

```c
aclError acltdtQueryQueueRoutes(const acltdtQueueRouteQueryInfo *queryInfo, acltdtQueueRouteList *qRouteList)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| queryInfo | 输入 | 查询条件。需 CreateQueueRouteQueryInfo 创建。 |
| qRouteList | 输入&输出 | 路由关系数组。需 CreateQueueRouteList 创建。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/tdt_queue/1_queue_route/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_queue/1_queue_route/main.cpp#L139)
