---
type: API
title: aclrtMemset
description: 按字节同步填充 Host/Device 内存为指定值；同步执行，不隐式做流或 Device 同步。
tags:
- task.lookup
- topic.data_movement.memory_access
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
# aclrtMemset

## 功能说明

同步初始化内存为指定值。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- aclrtMemsetImpl 调用 rtMemset 实现。

## 函数原型

```c
aclError aclrtMemset(void *devPtr, size_t maxCount, int32_t value, size_t count)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| devPtr | 输入 | 内存起始地址指针 |
| maxCount | 输入 | 内存最大长度，单位 Byte |
| value | 输入 | 设置的值 |
| count | 输入 | 需设置为指定值的内存长度，单位 Byte |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 同步执行，内部不会隐式 Device 同步或流同步
- 支持 Host 和 Device 两侧内存，Host 内存非锁页时可能导致未定义行为

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/device/2_device_P2P/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/device/2_device_P2P/main.cpp#L48)
- [`1_basic_features/memory/12_cross_server_physical_memory_sharing_withoutpid/client.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/12_cross_server_physical_memory_sharing_withoutpid/client.cpp#L57)
- [`1_basic_features/memory/12_cross_server_physical_memory_sharing_withoutpid/server.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/12_cross_server_physical_memory_sharing_withoutpid/server.cpp#L100)
