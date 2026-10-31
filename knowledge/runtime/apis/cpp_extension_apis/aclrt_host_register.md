---
type: API
title: aclrtHostRegister
description: "C++ Host 内存注册模板：type 重载直接返回 Device 指针，flag 重载支持映射或将非锁页内存注册为锁页内存。"
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
- '950'
- a3
- a2
---

# aclrtHostRegister

## 功能说明

注册Host内存地址。取消注册需调用aclrtHostUnregister接口。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口[aclrtHostRegister](../memory_management/aclrt_host_register.md)或aclrtHostRegisterV2。

## 函数原型

```cpp
template <typename T>
aclError aclrtHostRegister(T *ptr, uint64_t size, aclrtHostRegisterType type, T **devPtr)

template <typename T>
aclError aclrtHostRegister(T *ptr, uint64_t size, uint32_t flag)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| ptr | 输入 | Host内存地址。<br>支持直接传入通过aclrtMallocHost或aclrtMallocHostWithCfg接口申请的Host内存地址，也支持对该Host内存地址进行地址偏移后传入，但偏移后的内存地址需要满足4KB页对齐要求。<br>当os内核版本为5.10或更低时，使用非锁页内存会导致异常，因此必须调用aclrtMallocHost或aclrtMallocHostWithCfg接口来申请Host锁页内存。<br>当os内核版本为5.10以上时，支持使用非锁页的Host内存，因此既支持调用aclrtMallocHost或aclrtMallocHostWithCfg接口申请Host锁页内存，也支持使用malloc接口申请Host非锁页内存。使用malloc接口申请的Host内存无需4KB页对齐。 |
| size | 输入 | 内存大小，单位Byte。 |
| type | 输入 | 内存注册类型。类型定义请参见aclrtHostRegisterType。 |
| devPtr | 输出 | Host内存映射成的Device可访问的内存地址。<br>该地址仅支持在Device上访问，例如作为核函数的参数，供Device的AI Core访问。若涉及Host侧的内存处理，需使用原始Host内存地址。 |
| flag | 输入 | 内存注册类型。<br>取值为如下宏，支持配置单个宏，也支持配置多个宏位或（例如ACL_HOST_REG_MAPPED \| ACL_HOST_REG_PINNED）。<br><br>  - ACL_HOST_REG_MAPPED：将Host内存映射注册为Device可访问的内存地址，再配合调用aclrtHostGetDevicePointer接口获取映射后的Device内存地址。<br>  - ACL_HOST_REG_IOMEMORY：将Host上第三方PCIe设备的IO space(寄存器、缓存)映射注册为Device可访问，包括读写。使用该宏时不支持锁页内存，因此该宏不能与ACL_HOST_REG_PINNED组合使用。<br>  - ACL_HOST_REG_READONLY：Host内存映射注册为Device只读。预留选项，当前不支持。<br>  - ACL_HOST_REG_PINNED：将Host非锁页内存注册为锁页内存。Host非锁页内存可通过C/C++标准库函数（如malloc、calloc、new）或默认的mmap系统调用等方式申请。该宏仅适用于Host非锁页内存；若传入Host锁页内存，接口将返回错误。<br><br><br>宏定义如下：<br>#define ACL_HOST_REG_MAPPED 0x2UL<br>#define ACL_HOST_REG_IOMEMORY 0x4UL<br>#define ACL_HOST_REG_READONLY 0x8UL<br>#define ACL_HOST_REG_PINNED 0X10000000UL |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。
