---
type: API
title: aclrtSetStreamOverflowSwitch
description: "设置指定 Stream 后续新任务的溢出检测开关，已下发任务不变；关闭后不能通过溢出检测算子获取溢出结果。"
tags:
- task.lookup
- topic.precision
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
- 'a3'
- 'a2'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtSetStreamOverflowSwitch

## 功能说明

对接上层训练框架（如 PyTorch）时，针对指定 Stream 打开或关闭溢出检测开关。关闭后无法通过溢出检测算子获取任务是否溢出。

内部行为 （固定 commit `b523035a` 源码结论）：

- ACL 层校验 flag 为 0 或 1，无效值返回 ACL_ERROR_INVALID_PARAM。
- 委托 `rtSetStreamOverflowSwitch(stream, flag)` 到 RTS 层。

## 函数原型

```c
aclError aclrtSetStreamOverflowSwitch(aclrtStream stream, uint32_t flag)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 待操作 Stream。 |
| flag | 输入 | 溢出检测开关：0=关闭，1=打开。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 仅 950、A3、A2 支持。
- 打开/关闭仅对后续新下发的任务生效，已下发的任务维持原样。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`4_reliability/overflow_detection/0_overflow_detection/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/4_reliability/overflow_detection/0_overflow_detection/main.cpp#L115)
