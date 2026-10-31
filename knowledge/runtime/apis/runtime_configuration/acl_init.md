---
type: API
title: aclInit
description: 初始化 ACL 环境。进程内支持多次调用，配置内容必须一致；引用计数维护首次有效配置，重复调用返回 ACL_ERROR_REPEAT_INITIALIZE。
tags:
- task.lookup
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/02_initialization_and_deinitialization.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/acl.cpp
  role: implementation
source_headers:
- include/external/acl/acl.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclInit

## 功能说明

初始化函数。使用 acl 接口开发应用时，必须先调用 aclInit，否则后续系统内部资源初始化失败。可通过 json 配置文件开启 Dump、Profiling、默认 Device、栈空间等功能；满足默认需求时传入 NULL。

## 函数原型

```c
aclError aclInit(const char *configPath);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| configPath | 输入 | 配置文件路径（含文件名）的指针，json 格式。传入 NULL 或空 json 使用默认配置。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误/返回值 | 触发点 | 调用方处理 |
| --- | --- | --- |
| `ACL_ERROR_REPEAT_INITIALIZE` | 已初始化（aclInitRefCount > 0），增加计数后返回 | 若已知已初始化可忽略该错误 |
| `ACL_ERROR_INVALID_PARAM` | 配置文件内容与首次调用不一致（hash 校验失败） | 修正配置内容一致后再重试 |
| `ACL_ERROR_INTERNAL_ERROR` | SoC 版本获取失败（socName == nullptr） | 检查驱动/固件安装 |
| `ACL_GET_ERRCODE_RTS(rtErr)` | Dump/DefaultDevice 等内部 RTS 操作失败 | 按日志中内部错误码排查 |

转换为外部 `aclError` 数值经错误码映射，排查以日志中的内部符号为准。

## 约束说明

- 一个进程内支持多次调用 aclInit，但需与 [aclFinalize](acl_finalize.md) 或 [aclFinalizeReference](acl_finalize_reference.md) 配对去初始化。
- 重复调用时配置必须保持一致，否则首次有效、后续返回 ACL_ERROR_INVALID_PARAM。
- 重复调用 aclInit 返回 ACL_ERROR_REPEAT_INITIALIZE，可忽略继续业务。
- 多线程场景由调用方保证适当的同步（接口内部使用 `std::recursive_mutex`）。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/0_hello_cann/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/0_hello_cann/main.cpp#L91)
- [`0_quickstart/1_error_handling/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/1_error_handling/main.cpp#L51)
- [`0_quickstart/2_system_info/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/2_system_info/main.cpp#L44)
