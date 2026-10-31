---
type: API
title: aclrtMemcpyAsync
description: 下发到指定 Stream 的内存复制；锁页内存下为异步、需 Stream 同步等待完成，非锁页内存下同步返回。
tags:
- task.lookup
- topic.data_movement.data_copy
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-03_memory_copy_and_set.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/memory.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-30T07:38:42Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# aclrtMemcpyAsync

## 功能说明

实现内存复制的异步接口。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- aclrtMemcpyAsyncImpl 将参数组装后下发到 Stream 队列。

## 函数原型

```c
aclError aclrtMemcpyAsync(void *dst, size_t destMax, const void *src, size_t count, aclrtMemcpyKind kind, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| dst | 输入 | 目的内存地址指针 |
| destMax | 输入 | 目的内存最大长度，单位 Byte |
| src | 输入 | 源内存地址指针 |
| count | 输入 | 内存复制的长度，单位 Byte |
| kind | 输入 | 内存复制类型，见 `aclrtMemcpyKind` |
| stream | 输入 | 指定执行复制任务的 Stream |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 锁页内存下为异步接口，调用后需 Stream 同步等待完成
- 非锁页内存下同步返回
- EP 形态不支持异步 HOST_TO_HOST 复制
- RC/Control CPU 形态下 HOST_TO_DEVICE/DEVICE_TO_HOST 转为 DEVICE_TO_DEVICE

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/memory/2_h2d_async_memory_copy/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/2_h2d_async_memory_copy/main.cpp#L45)
- [`1_basic_features/memory/4_d2h_async_memory_copy/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/4_d2h_async_memory_copy/main.cpp#L45)
- [`1_basic_features/memory/6_d2d_async_memory_copy/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/6_d2d_async_memory_copy/main.cpp#L45)

## 配套 API 与常见组合

- [aclrtCreateStream](../stream_management/aclrt_create_stream.md)——异步拷贝必须指定一个有效 Stream 作为下发队列，用于约束与其它任务的先后顺序
- [aclrtSynchronizeStream](../stream_management/aclrt_synchronize_stream.md)——接口返回仅表示任务已下发，目标数据就绪须等该 Stream 同步完成后才成立
