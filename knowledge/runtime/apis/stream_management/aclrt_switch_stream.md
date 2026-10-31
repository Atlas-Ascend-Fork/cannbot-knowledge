---
type: API
title: aclrtSwitchStream
description: "比较 Device 内存中的条件值并异步跳转到目标 Stream，成功后当前流停止执行；falseStream 必须为 NULL。"
tags:
- task.lookup
- topic.graph_execution
- topic.implementation.synchronization
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/06_stream_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/stream.cpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/api_c_stream.cc
  role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a2'
- '310b'
- '310p'
- '910'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtSwitchStream

## 功能说明

根据条件在 Stream 之间跳转。异步接口。跳转成功后，只执行所跳转的 Stream 上的任务，当前 Stream 上的任务停止执行。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtsSwitchStream(leftValue, cond, rightValue, dataType, trueStream, falseStream, stream)` 到 RTS 层。ACL 层校验 leftValue、rightValue、trueStream、stream 非 NULL，falseStream 必须为 NULL。

## 函数原型

```c
aclError aclrtSwitchStream(void *leftValue, aclrtCondition cond, void *rightValue, aclrtCompareDataType dataType, aclrtStream trueStream, aclrtStream falseStream, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| leftValue | 输入 | 左值数据的 Device 内存地址。 |
| cond | 输入 | 比较条件（aclrtCondition）。 |
| rightValue | 输入 | 右值数据的 Device 内存地址。 |
| dataType | 输入 | 比较数据类型（aclrtCompareDataType）。 |
| trueStream | 输入 | 条件成立时执行的 Stream。 |
| falseStream | 输入 | 预留参数，当前固定传 NULL。 |
| stream | 输入 | 执行跳转任务的 Stream。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- A3 不支持。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/model_ri/2_model_switch/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/2_model_switch/main.cpp#L156)
