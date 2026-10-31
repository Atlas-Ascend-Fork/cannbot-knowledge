---
type: API
title: aclFinalizeReference
description: 按引用计数去初始化。与 aclInit 成对调用：Init 加一、FinalizeReference 减一，计数归零时真正释放资源并返回最终计数值。
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
# aclFinalizeReference

## 功能说明

去初始化函数，按引用计数释放资源。与 [aclInit](acl_init.md) 成对使用：[aclInit](acl_init.md) 每调用一次计数加一，本接口每调用一次计数减一，减到零时执行真正去初始化。[aclFinalize](acl_finalize.md) 则直接将计数清零一次清理。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclFinalizeReferenceImpl` 获取递归锁，读取当前计数 `aclInitRefCount`。
- 若 `refCount` 非空，写入当前计数。
- 若计数大于 1：计数减一并返回成功（未触发真正清理）。
- 若计数小于 1：返回 `ACL_ERROR_REPEAT_FINALIZE`。
- 若计数等于 1：调用 `aclFinalizeInternal()` 执行完整资源清理，再将计数置 0 返回。

## 函数原型

```c
aclError aclFinalizeReference(uint64_t *refCount);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| refCount | 输入&输出 | 返回调用后的引用计数。不需要获取时可传 nullptr。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 | 触发点 | 调用方处理 |
| --- | --- | --- |
| `ACL_ERROR_REPEAT_FINALIZE` | 引用计数已为零（无匹配的 [aclInit](acl_init.md)） | 检查 Init/Finalize 调用配对 |
| `ACL_ERROR_INTERNAL_ERROR` | `aclFinalizeInternal` 阶段失败 | 检查 Dump/Profiling 等配置 |

## 约束说明

- 必须与 [aclInit](acl_init.md) 成对调用，顺序（支持顺序与并发）均可，但计数必须匹配。
- 应用进程退出前必须确保已调用 [aclFinalize](acl_finalize.md) 或本接口完成去初始化。
- 不建议在析构函数中调用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/5_runtime_lifecycle_callbacks/0_reference_counted_plugin_lifecycle/plugin_lifecycle.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/5_runtime_lifecycle_callbacks/0_reference_counted_plugin_lifecycle/plugin_lifecycle.cpp#L142)
