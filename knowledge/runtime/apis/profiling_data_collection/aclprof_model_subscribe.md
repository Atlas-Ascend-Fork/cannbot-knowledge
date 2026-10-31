---
type: API
title: aclprofModelSubscribe
description: "按模型 ID 和订阅配置采集算子名称、类型、耗时；须与 UnSubscribe 配对，不能与 Init/Start/Stop/Finalize 采集流程混用。"
tags:
- task.lookup
- topic.performance.analysis
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/19-03_subscription_to_operator_information.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_prof.h
  role: header
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

# aclprofModelSubscribe

## 功能说明

网络场景下订阅算子的基本信息，包括算子名称、算子类型、执行耗时等。需与 [aclprofModelUnSubscribe](aclprof_model_unsubscribe.md) 配对使用。

## 函数原型

```c
aclError aclprofModelSubscribe(uint32_t modelId, const aclprofSubscribeConfig *profSubscribeConfig)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| modelId | 输入 | 待订阅的模型 ID |
| profSubscribeConfig | 输入 | 订阅配置，通过 [aclprofCreateSubscribeConfig](../operation_apis/aclprof_create_subscribe_config.md) 创建 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 与 [aclprofModelUnSubscribe](aclprof_model_unsubscribe.md) 配对使用。
- 不能在 Profiling 数据采集接口（Init/Start/Stop/Finalize）之间调用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/profiling/2_subscribe_model/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/2_subscribe_model/main.cpp#L107)
