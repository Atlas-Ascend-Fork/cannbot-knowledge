---
type: API
title: aclprofDestroyStepInfo
description: "释放 CreateStepInfo 创建的 Profiling 迭代信息对象；同一对象不能重复销毁。"
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

# aclprofDestroyStepInfo

## 功能说明

销毁通过[aclprofCreateStepInfo](aclprof_create_step_info.md)接口创建的aclprofStepInfo类型的数据。

## 函数原型

```c
void aclprofDestroyStepInfo(aclprofStepInfo* stepinfo)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| stepinfo | 输入 | 指定迭代信息。需提前调用[aclprofCreateStepInfo](aclprof_create_step_info.md)接口创建[aclprofStepInfo](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_prof.h#L108)类型的数据。 |

## 返回值说明

返回0表示成功，返回其他值表示失败。


## 约束说明

- 与[aclprofCreateStepInfo](aclprof_create_step_info.md)接口配对使用，先调用[aclprofCreateStepInfo](aclprof_create_step_info.md)接口再调用aclprofDestroyStepInfo接口。
- 同一aclprofStepInfo数据重复调用aclprofDestroyStepInfo接口，会出现重复释放内存的报错。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/profiling/1_msproftx/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/1_msproftx/main.cpp#L99)
