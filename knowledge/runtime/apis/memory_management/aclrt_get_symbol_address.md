---
type: API
title: aclrtGetSymbolAddress
description: "C 接口以 __gm__ 变量的符号地址查询实际 Device 地址，仅用于 Ascend C 毕昇混合编译，地址仅对当前 Device 有效。"
tags:
- task.lookup
- topic.implementation.resource_query
- topic.memory
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-11_device_variable_memory_operation.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/memory.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310p'
---
# aclrtGetSymbolAddress

## 功能说明

获取 Device 变量的地址。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- aclrtGetSymbolAddressImpl 调用 runtime 获取符号地址。

## 函数原型

```c
aclError aclrtGetSymbolAddress(const void *symbol, void **devPtr)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| symbol | 输入 | Device 变量的地址（传入 __gm__ 声明的变量名取地址） |
| devPtr | 输出 | Device 变量的内存地址指针 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 仅适用于 Ascend C 自定义算子 + 毕昇编译器混合编译场景
- Device 变量地址仅当前 Device 有效
- 仅支持 AI Core 算子中的 Device 变量
