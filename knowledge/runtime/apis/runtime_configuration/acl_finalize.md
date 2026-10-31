---
type: API
title: aclFinalize
description: 去初始化函数，直接清空初始化引用计数并释放进程内 acl 使用的相关资源。与 aclInit 的配对方式为 N:1（多次 Init 后一次 Finalize 即清零）。
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
# aclFinalize

## 功能说明

去初始化函数，释放进程内 acl 接口使用的相关资源。多次调用 [aclInit](acl_init.md) 后一次 aclFinalize 即把引用计数直接清零触发真正清理，无需与 Init 按次数配对。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclFinalizeImpl` 获取递归锁后检查 `aclFinalizeFlag`；若已置位则返回 `ACL_ERROR_REPEAT_FINALIZE`，防止重复去初始化。
- 通过 `aclFinalizeInternal` 依次执行：DlogReportFinalize、资源统计遍历、Profiling 去注册、各模块 Finalize 回调（ACL_OP_COMPILER、ACL_MODEL、DVPP、OTHER）、Dump server 清理、kernel launch 填充函数注销、默认 Device 禁用。
- 最终设置 `aclFinalizeFlag = true`、`aclInitRefCount = 0`。
- 对于涉及 Device 业务日志回传到 Host 的场景，默认增加 2000ms 延时确保 ERROR/EVENT 级别日志完整回传。

## 函数原型

```c
aclError aclFinalize(void);
```

## 参数说明

无。

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 | 触发点 | 调用方处理 |
| --- | --- | --- |
| `ACL_ERROR_REPEAT_FINALIZE` | aclFinalizeFlag 已置位（已去初始化） | 避免在已去初始化进程上再次调用 |
| `ACL_ERROR_INTERNAL_ERROR` | Dump server uninit 回调失败 | 检查 Dump 配置 |
| `ACL_GET_ERRCODE_RTS(rtErr)` | 内部 RTS 操作失败（日志回传延时等） | 按内部错误码排查 |

对外 `aclError` 数值经错误码映射，排查以日志中的内部符号为准。

## 约束说明

- 应用进程退出前必须调用 aclFinalize 或 [aclFinalizeReference](acl_finalize_reference.md) 完成去初始化，否则可能导致异常报错。
- 不建议在析构函数中调用，否则进程退出时可能因单例析构顺序未知导致异常。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/0_hello_cann/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/0_hello_cann/main.cpp#L228)
- [`0_quickstart/1_error_handling/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/1_error_handling/main.cpp#L85)
- [`0_quickstart/2_system_info/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/2_system_info/main.cpp#L66)
