---
type: API
title: aclprofCreateStepInfo
description: "创建 Profiling 迭代信息对象，与 DestroyStepInfo 配对；同一对象的同一 tag 只能设置一次。"
tags:
- task.lookup
- topic.performance.analysis
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/25-03_Operation_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_prof.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/dfx/msprof/collector/dvvp/msprofiler/prof_acl_core.cpp
  role: implementation
source_headers:
- include/external/acl/acl_prof.h
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

# aclprofCreateStepInfo

## 功能说明

创建aclprofStepInfo对象，用于描述迭代信息。

## 函数原型

```c
aclprofStepInfo* aclprofCreateStepInfo()
```

## 参数说明

无

## 返回值说明

- 返回aclprofStepInfo类型的指针，表示成功。
- 返回nullptr，表示失败。


## 约束说明

- 使用[aclprofDestroyStepInfo](aclprof_destroy_step_info.md)接口销毁aclprofStepInfo类型的数据，如不销毁会导致内存未被释放。
- 与[aclprofDestroyStepInfo](aclprof_destroy_step_info.md)接口配对使用，先调用aclprofCreateStepInfo接口再调用[aclprofDestroyStepInfo](aclprof_destroy_step_info.md)接口。

> **说明：**
>同一个aclprofStepInfo对象、同一个tag只能设置一次，否则Profiling解析会出错。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/profiling/1_msproftx/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/1_msproftx/main.cpp#L91)
