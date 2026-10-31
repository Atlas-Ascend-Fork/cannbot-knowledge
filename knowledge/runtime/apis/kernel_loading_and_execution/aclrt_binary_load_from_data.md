---
type: API
title: aclrtBinaryLoadFromData
description: 从内存加载并解析算子二进制数据，输出指向算子二进制的binHandle。加载AI CPU算子信息时需配合 aclrtRegisterCpuFunc。
tags:
- task.lookup
- topic.implementation.kernel_launch
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.c_api
status: draft
sources:
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/14_Kernel_loading_and_execution.md
    role: primary
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
    role: header
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/kernel.cpp
    role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtBinaryLoadFromData

## 功能说明

从内存加载并解析算子二进制数据，输出指向算子二进制的binHandle。加载AI CPU算子信息时需配合 [aclrtRegisterCpuFunc](aclrt_register_cpu_func.md)。


委托 `rtsBinaryLoadFromData(...)` 到 RTS 层。
## 函数原型

```c
aclError aclrtBinaryLoadFromData(const void *data, size_t length, const aclrtBinaryLoadOptions *options, aclrtBinHandle *binHandle)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| data | 输入 | 存放算子二进制数据的Host内存地址。 |
| length | 输入 | 数据大小（Byte），必须大于0。 |
| options | 输入 | 加载可选参数：`aclrtBinaryLoadOptions`。 |
| binHandle | 输出 | 标识算子二进制的句柄。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

系统仅将算子加载至当前Context对应的Device上。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/kernel/6_memory_loaded_vector_add/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/6_memory_loaded_vector_add/main.cpp#L63)
