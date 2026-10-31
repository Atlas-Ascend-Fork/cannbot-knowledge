---
type: API
title: aclrtMemAllocManaged
description: "C++ 模板申请 Host/Device 统一编址的 UVM 内存，大小向上按 2MB 对齐；返回类型化指针，使用 aclrtFree 释放。"
tags:
- task.lookup
- topic.implementation.memory_management
- topic.implementation.api_layer.cpp_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/26_cpp_extension_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt_api.h
  role: header
source_headers:
- include/external/acl/acl_rt_api.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- a2
---

# aclrtMemAllocManaged

## 功能说明

申请统一虚拟内存（Unified Virtual Memory, UVM），通过\*ptr返回已申请内存的指针，且申请的内存大小会根据用户指定的size向上按2MB对齐。使用本接口申请的内存，若需释放内存，需调用aclrtFree接口。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtMemAllocManaged。

## 函数原型

```cpp
template <typename T>
aclError aclrtMemAllocManaged(T **devPtr, size_t size, uint32_t flags = ACL_RT_MEM_ATTACH_GLOBAL)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| devPtr | 输出 | “已分配内存的指针”的指针，由于Host和Device虚拟地址统一编址，该参数不区分申请位置。 |
| size | 输入 | 内存大小，单位Byte。<br>size不能为0，单个应用进程最大可申请3TB UVM类型的虚拟内存。 |
| flag | 输入 | 内存标识。<br>当前flag仅支持设置为ACL_RT_MEM_ATTACH_GLOBAL，所对应数值为1。设置为ACL_RT_MEM_ATTACH_GLOBAL后，通过本接口申请的内存在Device和Host侧都可以被访问。<br>宏定义如下：<br>#define ACL_RT_MEM_ATTACH_GLOBAL (0x01U) |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。


## 约束说明

约束与C接口aclrtMemAllocManaged接口保持一致。
