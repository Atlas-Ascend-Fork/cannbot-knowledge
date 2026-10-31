---
type: API
title: aclrtDeviceEnablePeerAccess
description: 开启当前 Device 到指定 peer Device 的单向 P2P 数据交互；flags 必须为 0，ACL 层取当前 Device 并把 peerDeviceId 转成物理 ID 后调用 rtEnableP2P，Device 级单向生效。
tags:
- task.lookup
- topic.data_movement.memory_access
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/04_device_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/memory.cpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/api_c_device.cc
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/impl/api_impl.cc
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-28T07:09:42Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- a3
- a2
- '310p'
- '910'
---

# aclrtDeviceEnablePeerAccess

## 功能说明

开启当前 Device 与指定 Device 之间的数据交互（P2P）。开启是 **Device 级且单向** 的：以 Device 0 调用并指定 peer Device 1，则仅 0→1 方向可用；要启用反向需先切换到 Device 1，再以 peer Device 0 调用一次。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- ACL 层 `aclrtDeviceEnablePeerAccessImpl` 先用 `ACL_CHECK_RESERVED_PARAM_REPORT_RET(flags, 0U, ...)` 校验 `flags`，非 0 返回 `ACL_ERROR_FEATURE_UNSUPPORTED`；再通过 `rtGetDevice` 取当前 Device ID，拒绝其与 `peerDeviceId` 相等；随后用 `rtGetDevicePhyIdByIndex` 把 `peerDeviceId` 转成物理 ID，调用 `rtEnableP2P(currentDeviceId, peerPhyId, flags)`。
- RTS 层 `ApiImpl::EnableP2P` 仅做日志后直接委托 `NpuDriver::EnableP2P`，本层无额外能力判断。
- 因此本接口依赖当前线程/Context 的 Device 绑定：当前 Device 由内部 `rtGetDevice` 决定，不由参数指定。

## 函数原型

```c
aclError aclrtDeviceEnablePeerAccess(int32_t peerDeviceId, uint32_t flags);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| peerDeviceId | 输入 | 指定 peer Device ID，不能与当前 Device 的 ID 相同。范围 `[0, 可用 Device 数量-1]`。 |
| flags | 输入 | 保留参数，当前必须设置为 0。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 / 返回 | 对外 aclError | 触发点 |
| --- | --- | --- |
| —（ACL 层直接返回） | `ACL_ERROR_FEATURE_UNSUPPORTED` | `flags` 不为 0 |
| —（ACL 层直接返回） | `ACL_ERROR_INVALID_PARAM`（100000） | 当前 Device ID 等于 `peerDeviceId` |
| 驱动/内部码 | 经 `ErrorcodeManage::GetRtExtErrCode` 映射 | 取当前 Device、物理 ID 反查或驱动使能失败 |

未登记的内部码（不小于 `RT_ERRORCODE_BASE`）统一落到 `ACL_ERROR_RT_INTERNAL_ERROR`（507000）。

## 约束说明

- 开启前建议先用 [aclrtDeviceCanAccessPeer](aclrt_device_can_access_peer.md) 探测能力；关闭对应方向使用 `aclrtDeviceDisablePeerAccess`。
- 支持的连接范围与场景限制同 [aclrtDeviceCanAccessPeer](aclrt_device_can_access_peer.md)（同一 PCIe Switch / 同机同容器 / 同进程线程间）。
- 开启是单向的；双向通信需要在两个 Device 上分别调用并指定相反的 peer。
- 产品支持范围不含 Atlas 200I/500 A2 推理产品（`310b`）。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/device/2_device_P2P/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/device/2_device_P2P/main.cpp#L41)：查询通过后开启当前 Device 到 peer Device 的数据交互。
