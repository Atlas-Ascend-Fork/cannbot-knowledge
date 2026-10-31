---
type: API
title: aclrtTaskUpdateAsync
description: "异步刷新模型绑定流中的指定任务；taskStream 与 taskId 标识待刷新任务，execStream 指定执行刷新任务的流。"
tags:
- task.lookup
- topic.graph_execution
- topic.implementation.api_layer.c_api
status: draft
sources:
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/12_execution_control.md
    role: primary
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
    role: header
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/kernel.cpp
    role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310p'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtTaskUpdateAsync

## 功能说明

刷新目标任务的信息。异步接口。

内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- 委托 `rtsLaunchUpdateTask(taskStream, taskId, execStream, reinterpret_cast<rtTaskUpdateCfg_t*>(info))` 到 RTS 层。
## 函数原型

```c
aclError aclrtTaskUpdateAsync(aclrtStream taskStream, uint32_t taskId, aclrtTaskUpdateInfo *info, aclrtStream execStream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| taskStream | 输入 | 目标任务所在的Stream。仅支持与模型绑定过的Stream。 |
| taskId | 输入 | 目标任务ID，可通过 [aclrtGetThreadLastTaskId](aclrt_get_thread_last_task_id.md) 获取。 |
| info | 输入 | 配置信息：aclrtTaskUpdateInfo。 |
| execStream | 输入 | 执行刷新任务的Stream。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明
