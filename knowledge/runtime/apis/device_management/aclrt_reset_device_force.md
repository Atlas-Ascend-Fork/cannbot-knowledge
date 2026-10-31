---
type: API
title: aclrtResetDeviceForce
description: 强制复位 Device，一次调用即清空该 Device 全部 Primary Context 保留引用并拆除默认 Context，无需与 aclrtSetDevice 次数配对；无引用可清空时返回错误，多线程下应由单一 owner 调用一次。
tags:
- task.lookup
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/04_device_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/device.cpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/impl/api_error.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/impl/api_impl.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/src/runtime.cc
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

# aclrtResetDeviceForce

## 功能说明

强制复位当前运算的 Device，释放 Device 上的资源，释放范围与 [aclrtResetDevice](aclrt_reset_device.md) 相同（默认 Context、默认 Stream 及默认 Context 下创建的所有 Stream），同样会等待未完成的任务结束后再释放。

与普通 Reset 的关键差别在于**不按次递减，而是一次清空**：

```
# 与 SetDevice 配对使用
aclrtSetDevice(1) -> aclrtResetDeviceForce(1) -> aclrtSetDevice(1) -> aclrtResetDeviceForce(1)

# 与 SetDevice 不配对使用：多次 Set 后一次 Force 即可
aclrtSetDevice(1) -> aclrtSetDevice(1) -> aclrtResetDeviceForce(1)
```

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- 调用链为 `aclrtResetDeviceForceImpl` → `rtDeviceResetForce` → `ApiErrorDecorator::DeviceResetForce` → `ApiImpl::DeviceResetForce` → `ResetDeviceForce` → `DeviceReset(devId, isForceReset=true)` → `Runtime::PrimaryContextRelease(devId, true)`。与普通 Reset 相比，Force 路径在 `ApiErrorDecorator` 中**没有** `RT_ERROR_CONTEXT_DEL` 的 EE1018 外部提示分支，错误原样上抛。
- `DecideForcePrimaryReleaseAction` 先取 Primary Context 对象：`ctx` 为空（该 Device 从未建立默认 Context）时记 `RETURN_ERROR`；否则调用 `MarkPrimaryRefUpdatingForForceReset` **排空全部保留引用**（内部循环 `TryDecRef` 直到计数切换到更新态）。因此无论此前 SetDevice 过几次，一次 Force 都能把计数清零。
- `RETURN_ERROR` 在 `ReleasePrimaryContextSlot` 中统一转成 `RT_ERROR_CONTEXT_DEL`；这解释了"该 Device 已无资源可释放时 Force 报错"的行为。
- 拆除失败不会静默丢计数：`RollbackPrimaryTearDown` 会把本次排空的保留引用按 `retainRestoreCount` 恢复，并还原原 force 标记。
- `sentinelMode` 下 `tsId == RT_TSC_ID` 的槽位直接跳过，不参与拆除。

## 函数原型

```c
aclError aclrtResetDeviceForce(int32_t deviceId);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| deviceId | 输入 | Device ID，按用户可见编号解释。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误（rtError_t 符号） | 对外 aclError | 触发点 |
| --- | --- | --- |
| `RT_ERROR_DEVICE_ID` | `ACL_ERROR_RT_INVALID_DEVICEID`（107001） | 用户 Device ID 换算驱动 ID 失败，或驱动 Device ID 越界/非法 |
| `RT_ERROR_CONTEXT_DEL` | `ACL_ERROR_RT_CONTEXT_RELEASE_ERROR`（507007） | 该 Device 上已无默认 Context 或已无保留引用可排空（重复 Force、被其他线程先释放等） |
| 未登记的内部码且不小于 `RT_ERRORCODE_BASE` | `ACL_ERROR_RT_INTERNAL_ERROR`（507000） | 映射表兜底 |

数值映射在 RTS 层完成（`ErrorcodeManage::GetRtExtErrCode`），ACL 层的 `ACL_GET_ERRCODE_RTS` 是恒等宏。排查以日志中的内部符号与"total ref count is 0"等提示为准。

## 约束说明

- **多线程下只能由一个 owner 调用一次**。文档给出的反例是：线程 1 与线程 2 都先 `aclrtSetDevice(1)`，线程 1 先 `aclrtResetDeviceForce(1)` 释放后，线程 2 再调用会报错——因为资源已被释放，其保留引用已不存在。正确做法是在线程执行的最后统一调用一次。
- 与 [aclrtResetDevice](aclrt_reset_device.md) 可以混用，但必须满足"两个 Reset 各与 Set 配对，且 Force 在普通 Reset 之后"，否则报错。例如 `Set -> Set -> Reset -> Reset` 时计数已在第二个 Reset 归零，后续再调用任一 Reset 都会报错；`Set -> Set -> Force -> Reset` 因 Force 在前同样报错。
- 不能靠"先 Force 再 Reset"来补计数：Force 排空的是全部保留引用，之后没有可供普通 Reset 递减的计数。
- 释放会等待默认 Context/Stream 上的任务完成，可能阻塞较长时间。
- 显式创建的 Event/Stream/Context 仍建议在复位前按 Destroy 顺序释放，否则可能导致业务异常。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/0_hello_cann/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/0_hello_cann/main.cpp#L224)
- [`0_quickstart/1_error_handling/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/1_error_handling/main.cpp#L84)
- [`0_quickstart/3_cross_version/0_runtime_compatibility/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/3_cross_version/0_runtime_compatibility/main.cpp#L95)

## 配套 API 与常见组合

- [aclrtSetDevice](aclrt_set_device.md)——强制释放会一次清空该 Device 的 Primary Context 引用计数，与按次数的 Set 不对称
- [aclrtResetDevice](aclrt_reset_device.md)——多线程共享默认 Context 时优先用按计数的普通 Reset，避免影响其它线程
