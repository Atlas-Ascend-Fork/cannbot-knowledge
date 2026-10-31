---
type: API
title: aclrtRandomNumAsync
description: 下发并执行随机数生成任务。异步接口。
tags:
- task.lookup
- topic.compute.random_sampling
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
updated_at: '2026-10-29T08:46:01Z'
platforms:
- 'a3'
- 'a2'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtRandomNumAsync

## 功能说明

下发并执行随机数生成任务。异步接口。

内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- 校验 dataType 在映射表中存在；将 aclDataType 映射为 rtDataType；委托 `rtsLaunchRandomNumTask` 到 RTS 层。
## 函数原型

```c
aclError aclrtRandomNumAsync(const aclrtRandomNumTaskInfo *taskInfo, const aclrtStream stream, void *reserve)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| taskInfo | 输入 | 随机数生成任务信息。 |
| stream | 输入 | 执行随机数生成任务的Stream。 |
| reserve | 输入 | 预留参数，当前固定传NULL。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/built_in_task/1_random_num_task/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/built_in_task/1_random_num_task/main.cpp#L182)
