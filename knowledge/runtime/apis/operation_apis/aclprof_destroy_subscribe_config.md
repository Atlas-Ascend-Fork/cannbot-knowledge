---
type: API
title: aclprofDestroySubscribeConfig
description: "释放 CreateSubscribeConfig 创建的算子性能订阅配置；同一配置指针不能重复销毁。"
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
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/dfx/msprof/collector/dvvp/msprofiler/prof_api_common.cpp
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

# aclprofDestroySubscribeConfig

## 功能说明

销毁通过[aclprofCreateSubscribeConfig](aclprof_create_subscribe_config.md)接口创建的aclprofSubscribeConfig类型的数据。

## 函数原型

```c
aclError aclprofDestroySubscribeConfig(const aclprofSubscribeConfig *profSubscribeConfig)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| profSubscribeConfig | 输入 | 待销毁的aclprofSubscribeConfig类型的指针。类型定义请参见[aclprofSubscribeConfig](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_prof.h#L107)。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。


## 约束说明

- 与[aclprofCreateSubscribeConfig](aclprof_create_subscribe_config.md)接口配对使用，先调用[aclprofCreateSubscribeConfig](aclprof_create_subscribe_config.md)接口再调用aclprofDestroySubscribeConfig接口。
- 同一aclprofSubscribeConfig指针重复调用aclprofDestroySubscribeConfig接口，会出现重复释放内存的报错。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/profiling/2_subscribe_model/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/2_subscribe_model/main.cpp#L130)
