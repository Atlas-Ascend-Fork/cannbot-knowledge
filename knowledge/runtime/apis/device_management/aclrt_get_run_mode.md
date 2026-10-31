---
type: API
title: aclrtGetRunMode
description: 获取当前 AI 软件栈的运行模式；内部把驱动的 OFFLINE 与 AICPU_SCHED 两种模式都归为 ACL_DEVICE，其余一律归为 ACL_HOST，且不依赖 Context、实现路径上不会失败。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/04_device_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/device.cpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/impl/api_impl.cc
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-14T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# aclrtGetRunMode

## 功能说明

获取当前 AI 软件栈的运行模式，用于区分 Host 侧运行与 Device 侧（离线/嵌入式）运行。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- 本接口**不需要 Context**：`ApiImpl::GetRunMode` 直接读取驱动运行模式（`NpuDriver::RtGetRunMode()`），不取当前 Context，也不需要先 `aclrtSetDevice`。
- 驱动侧 `rtRunMode` 有四个取值（`RT_RUN_MODE_OFFLINE`/`ONLINE`/`AICPU_SCHED`/`RESERVED`），Runtime 先把 `RT_RUN_MODE_AICPU_SCHED` 归一为 `RT_RUN_MODE_OFFLINE`，再交给 ACL 层。
- ACL 层只做二值判定：`RT_RUN_MODE_OFFLINE` → `ACL_DEVICE`；**其余一切取值 → `ACL_HOST`**。这是"非离线即 Host"的兜底判定，不是逐值映射。
- `ApiImpl::GetRunMode` 无条件返回 `RT_ERROR_NONE`，因此除入参为空指针外，本接口在实现路径上没有失败分支。

## 函数原型

```c
aclError aclrtGetRunMode(aclrtRunMode *runMode);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| runMode | 输出 | 运行模式的指针，由接口写入。类型定义见 `aclrtRunMode`。 |

`aclrtRunMode` 的两个取值按声明顺序为 `ACL_DEVICE = 0`、`ACL_HOST = 1`。`ACL_DEVICE` 的枚举值是 0，未初始化的变量读出来会与它同值，判定时不要依赖"零值即未设置"。

## 返回值说明

返回 0 表示成功，其他值表示失败。实现上唯一可区分的失败场景：

| 内部错误（rtError_t 符号） | 对外 aclError | 触发点 |
| --- | --- | --- |
| —（ACL 层直接返回） | `ACL_ERROR_INVALID_PARAM`（100000） | `runMode` 为空指针 |

`ACL_ERROR_INVALID_PARAM` 是 ACL 层错误码，不参与 rtError 映射；驱动的运行模式读取失败不会作为错误上抛，而是按上述兜底规则落到 `ACL_HOST`。

## 约束说明

- 结果是进程级的运行模式，不随 Device 或 Context 变化，因此不需要先 [aclrtSetDevice](aclrt_set_device.md)。
- 因为判定是"非 OFFLINE 即 ACL_HOST"，未来新增的驱动模式也会被归为 `ACL_HOST`；如果业务需要区分具体模式，不能只依赖本接口的返回值。
- 与 [aclrtGetDevice](aclrt_get_device.md) 不同：后者需要本线程已 SetDevice 或已有有效 Context，本接口无此要求，两者不构成依赖关系。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/1_error_handling/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/1_error_handling/main.cpp#L57)
- [`0_quickstart/2_system_info/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/2_system_info/main.cpp#L52)
- [`1_basic_features/device/1_device_multi_thread/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/device/1_device_multi_thread/main.cpp#L43)
