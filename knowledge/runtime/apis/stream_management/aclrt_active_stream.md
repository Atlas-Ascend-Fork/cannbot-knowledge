---
type: API
title: aclrtActiveStream
description: "在已绑定模型的 Stream 上异步激活另一条已绑定 Stream，使目标流任务与当前流并行执行。"
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

# aclrtActiveStream

## 功能说明

激活与模型绑定的 Stream。被激活的 Stream 上的任务与当前 Stream 上的任务并行执行。异步接口。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtsActiveStream(activeStream, stream)`（即 `rtStreamActive`）到 RTS 层。ACL 层校验参数非 NULL。

## 函数原型

```c
aclError aclrtActiveStream(aclrtStream activeStream, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| activeStream | 输入 | 待激活的 Stream。仅支持 [aclmdlRIBindStream](../model_running_instance_management/aclmdl_ri_bind_stream.md) 绑定过的 Stream。 |
| stream | 输入 | 执行激活任务的 Stream。仅支持绑定过的 Stream。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- A3 不支持。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/model_ri/2_model_switch/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/2_model_switch/main.cpp#L150)
