---
type: API
title: aclrtResetDevice
description: 复位指定 Device 并释放其默认 Context/Stream 资源；内部按 TS 槽位对该 Device 的 Primary Context 引用计数各减一，与 aclrtSetDevice 按次数配对，计数归零才真正释放，无引用可减时返回错误。
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

# aclrtResetDevice

## 功能说明

复位当前运算的 Device，释放 Device 上的资源。释放范围包括该 Device 的默认 Context、默认 Stream，以及默认 Context 下创建的所有 Stream。若默认 Context 或默认 Stream 上的任务尚未完成，系统会等待任务完成后再释放。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- ACL 层 `aclrtResetDeviceImpl` 是 `rtDeviceReset` 的直通包装，自身不做 Device ID 校验，错误按 `ACL_REQUIRES_RTS_OK` 直接上抛。
- RTS 层 `rtDeviceReset` → `ApiErrorDecorator::DeviceReset`：先用 `Runtime::ChgUserDevIdToDeviceId` 把用户 Device ID 换算成驱动 Device ID，再用 `CheckDeviceIdIsValid` 校验，最后进入 `ApiImpl::DeviceReset` → `Runtime::PrimaryContextRelease(devId, isForceReset=false)`。因此**参数与错误语义都基于"用户 Device ID"**，而引用计数按换算后的驱动 Device ID 维护。
- `PrimaryContextRelease` 对 `[0, tsNum_)` 的每个 TS 槽位各做一次 `RefObject<Context*>::TryDecRef`。只有递减后计数归零的槽位才进入 teardown；**任一槽位成功递减一次，本次调用即视为有效并返回 0**。所有槽位都没有可递减的引用时返回 `RT_ERROR_CONTEXT_DEL`。
- 结论：计数单位是"每个 TS 槽位一次"，普通 Reset 每次调用只对每个槽位减一；多 TS 平台上各槽位独立计数，不存在"一次 Reset 清空全部引用"的行为。

## 函数原型

```c
aclError aclrtResetDevice(int32_t deviceId);
```

## 参数说明

| 参数名   | 输入/输出 | 说明                                                                                        |
| -------- | --------- | ------------------------------------------------------------------------------------------- |
| deviceId | 输入      | Device ID。按用户可见编号解释，设置`ASCEND_RT_VISIBLE_DEVICES` 时按可见集合重排后的编号。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误（rtError_t 符号）                  | 对外 aclError                                    | 触发点                                                                          |
| ------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------- |
| `RT_ERROR_DEVICE_ID`                      | `ACL_ERROR_RT_INVALID_DEVICEID`（107001）      | 用户 Device ID 换算驱动 ID 失败，或驱动 Device ID 越界/非法                     |
| `RT_ERROR_CONTEXT_DEL`                    | `ACL_ERROR_RT_CONTEXT_RELEASE_ERROR`（507007） | 该 Device 上没有任何可递减的 Primary Context 引用（未 SetDevice，或计数已归零） |
| 未登记的内部码且不小于`RT_ERRORCODE_BASE` | `ACL_ERROR_RT_INTERNAL_ERROR`（507000）        | 映射表兜底                                                                      |

数值映射发生在 RTS 层（`GetRtExtErrCodeAndSetGlobalErr` → `ErrorcodeManage::GetRtExtErrCode`），ACL 层的 `ACL_GET_ERRCODE_RTS` 是恒等宏，不再改写数值，因此对外 `aclError` 与内部符号是多对一的映射关系。`RT_ERROR_CONTEXT_DEL` 会附带 EE1018 外部提示"设备尚未设置或已复位"。排查以日志中的内部符号及其 `retCode=%#x` 为准。

## 约束说明

- 与 [aclrtSetDevice](aclrt_set_device.md) 按次数配对使用：Set 每调用一次计数加一，Reset 每调用一次减一，计数减到 0 才真正释放 Device 资源。`aclrtResetDeviceForce` 则可一次清空计数。
- 计数已为零时再调用本接口返回错误，不会静默成功。
- 若该 Device 上存在显式创建的 Context、Stream、Event，复位前建议按 `aclrtDestroyEvent` → `aclrtDestroyStream` → `aclrtDestroyContext` → `aclrtResetDevice` 的顺序释放，否则可能导致业务异常。
- 复位会等待默认 Context/Stream 上未完成的任务结束后才释放，因此可能阻塞较长时间。
- 引用计数是进程级的：任一线程把计数复位到零，会使其他线程此前通过 SetDevice 建立的默认 Context 绑定失效。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/ipcevent/0_ipcevent/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/ipcevent/0_ipcevent/proc_a.cpp#L83)
- [`2_advanced_features/ipcevent/0_ipcevent/proc_b.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/ipcevent/0_ipcevent/proc_b.cpp#L97)
- [`2_advanced_features/ipcevent/1_ipcevent_multi_device/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/ipcevent/1_ipcevent_multi_device/proc_a.cpp#L116)

## 配套 API 与常见组合

- [aclrtSetDevice](aclrt_set_device.md)——与本接口按次数配对；只有把引用计数减到零才真正释放默认 Context 与资源
- [aclrtResetDeviceForce](aclrt_reset_device_force.md)——需要忽略计数一次性强制释放时，用强制变体替代
