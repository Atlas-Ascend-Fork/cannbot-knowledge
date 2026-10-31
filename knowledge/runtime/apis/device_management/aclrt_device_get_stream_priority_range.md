---
type: API
title: aclrtDeviceGetStreamPriorityRange
description: 查询 Stream 优先级的取值范围；固定实现直接返回常量（最低 7、最高 0），允许传入空指针并跳过对应输出，不向硬件发起查询。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/04_device_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/device.cpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/api_c_device.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/impl/api_impl.cc
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-28T07:09:42Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- a3
- a2
- '310b'
- '310p'
- '910'
---

# aclrtDeviceGetStreamPriorityRange

## 功能说明

查询硬件支持的 Stream 最低、最高优先级。数值语义与 [aclrtStreamGetPriority](../stream_management/aclrt_stream_get_priority.md) / `aclrtSetStreamAttribute` 的优先级参数一致：数值越小优先级越高。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- ACL 层 `aclrtDeviceGetStreamPriorityRangeImpl` 直接 `ACL_REQUIRES_RTS_OK(rtsDeviceGetStreamPriorityRange(...))`，**不做空指针校验**。
- RTS 层 `ApiImpl::DeviceGetStreamPriorityRange` 未查询驱动或硬件，而是直接写入常量：`*leastPriority = RT_STREAM_LEAST_PRIORITY`（7）、`*greatestPriority = RT_STREAM_GREATEST_PRIORITY`（0）；且对空指针做保护，`leastPriority`/`greatestPriority` 为 `nullptr` 时跳过对应输出并返回 `RT_ERROR_NONE`。
- 即传空指针不会报错，但也不会得到数值；这与需要非空输出指针的多数查询接口不同。

## 函数原型

```c
aclError aclrtDeviceGetStreamPriorityRange(int32_t *leastPriority, int32_t *greatestPriority);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| leastPriority | 输出 | 最低优先级（固定实现返回 7）。 |
| greatestPriority | 输出 | 最高优先级（固定实现返回 0）。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现返回常量且不访问硬件，主要失败来源是 Runtime 尚未初始化等内部错误，经 `ErrorcodeManage::GetRtExtErrCode` 映射后返回；未登记的内部码（不小于 `RT_ERRORCODE_BASE`）统一落到 `ACL_ERROR_RT_INTERNAL_ERROR`（507000）。

## 约束说明

- 数值越小优先级越高，因此 `leastPriority`（7）的数值大于 `greatestPriority`（0），不要按“最低=0”的直觉理解。
- 固定实现返回的是编译期常量，不代表具体产品可动态调整的优先级档位；跨版本或需要硬件真实档位时应重新核对实现。
- 查询本接口不需要先 `aclrtSetDevice`，也不要求已建立 Context。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/device/1_device_multi_thread/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/device/1_device_multi_thread/main.cpp#L63)：查询 Stream 优先级范围。
