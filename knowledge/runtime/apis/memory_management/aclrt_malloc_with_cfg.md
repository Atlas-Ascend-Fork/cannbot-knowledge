---
type: API
title: aclrtMallocWithCfg
description: "按 policy 和 cfg 申请 Device 线性内存，支持带宽类型、用户态只读与基础分配规则组合。"
tags:
- task.lookup
- topic.implementation.memory_management
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-01_device_memory_malloc_and_free.md
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
- '310b'
- '310p'
- '910'
---
# aclrtMallocWithCfg

## 功能说明

在 Device 上分配线性内存，支持通过 cfg 参数指定额外配置信息。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- aclrtMallocWithCfgImpl 将 policy 和 cfg 合并为 rtDrvMemProp_t 后调用 rtMemAlloc。

## 函数原型

```c
aclError aclrtMallocWithCfg(void **devPtr, size_t size, aclrtMemMallocPolicy policy, aclrtMallocConfig *cfg)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| devPtr | 输出 | Device 上已分配内存的指针的指针 |
| size | 输入 | 申请内存的大小，单位 Byte，不能为 0 |
| policy | 输入 | 内存分配规则，支持三种组合位或：高/低带宽 + 用户态只读 + 基础规则 |
| cfg | 输入 | 内存配置信息，不指定时传 NULL |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- policy 支持单个枚举项或多个位或，支持 ACL_MEM_TYPE_HIGH/LOW_BAND_WIDTH、ACL_MEM_ACCESS_USER_SPACE_READONLY 等组合
