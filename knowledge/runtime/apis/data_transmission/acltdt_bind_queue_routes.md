---
type: API
title: acltdtBindQueueRoutes
description: "批量绑定队列路由并返回各关系结果，全部成功才返回成功；禁止形成环路，不支持并发调用。"
tags:
- task.lookup
- topic.implementation.resource_lifecycle
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
# acltdtBindQueueRoutes

## 功能说明

绑定队列路由关系。

## 函数原型

```c
aclError acltdtBindQueueRoutes(acltdtQueueRouteList *qRouteList)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| qRouteList | 输入/输出 | 路由关系数组。调用后返回绑定结果。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。所有关系绑定成功才返回成功。

## 约束说明

校验是否成环，不允许成环。不支持并发调用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/tdt_queue/1_queue_route/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_queue/1_queue_route/main.cpp#L116)
