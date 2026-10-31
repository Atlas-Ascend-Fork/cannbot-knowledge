---
type: API
title: aclprofCreateSubscribeConfig
description: "创建算子性能订阅配置，指定采集开关和管道写指针；当前仅支持耗时统计，不支持 AicoreMetrics 采集。"
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

# aclprofCreateSubscribeConfig

## 功能说明

创建aclprofSubscribeConfig类型的数据，表示创建订阅配置信息。
如需销毁aclprofSubscribeConfig类型的数据，请参见[aclprofDestroySubscribeConfig](aclprof_destroy_subscribe_config.md)。

## 函数原型

```c
aclprofSubscribeConfig *aclprofCreateSubscribeConfig(int8_t timeInfoSwitch, aclprofAicoreMetrics aicoreMetrics, void *fd)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| timeInfoSwitch | 输入 | 是否采集网络模型中算子的性能数据：<br><br>  - 1：采集<br>  - 0：不采集<br><br>类型定义请参见[aclprofSubscribeConfig](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_prof.h#L107)和aclprofAicoreMetrics。 |
| aicoreMetrics | 输入 | 表示AI Core性能指标采集项。<br> 说明： 订阅接口目前仅提供算子耗时统计的功能，暂时不支持AicoreMetrics采集功能。<br>取值详见aclprofAicoreMetrics。 |
| fd | 输入 | 用户创建的管道写指针。<br>用户在调用[aclprofModelUnSubscribe](../profiling_data_collection/aclprof_model_unsubscribe.md)接口后，系统内部会在数据发送结束后，关闭该模型的管道写指针。 |

## 返回值说明

- 返回aclprofSubscribeConfig类型的指针，表示成功。
- 返回nullptr，表示失败。


## 约束说明

- 使用[aclprofDestroySubscribeConfig](aclprof_destroy_subscribe_config.md)接口销毁aclprofSubscribeConfig类型的数据，如不销毁会导致内存未被释放。
- 与[aclprofDestroySubscribeConfig](aclprof_destroy_subscribe_config.md)接口配对使用，先调用aclprofCreateSubscribeConfig接口再调用[aclprofDestroySubscribeConfig](aclprof_destroy_subscribe_config.md)接口。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/profiling/2_subscribe_model/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/2_subscribe_model/main.cpp#L105)
