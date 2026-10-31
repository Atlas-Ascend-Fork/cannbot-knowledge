---
type: API
title: aclrtDeviceCanAccessPeer
description: 查询两个 Device 之间是否支持 P2P 数据交互；ACL 层先拒绝 deviceId 等于 peerDeviceId，并把 peerDeviceId 转成物理 ID 再查询，芯片未开放 P2P、离线模式或无有效 Context 时会直接报错而不是返回 0。
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

# aclrtDeviceCanAccessPeer

## 功能说明

查询两个 Device 之间是否支持数据交互（P2P 访问），结果写入 `canAccessPeer`：1 表示支持，0 表示不支持。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- ACL 层 `aclrtDeviceCanAccessPeerImpl` 先拒绝 `deviceId == peerDeviceId`，直接返回 `ACL_ERROR_INVALID_PARAM`；随后用 `rtGetDevicePhyIdByIndex` 把 `peerDeviceId`（用户 Device ID）转成物理 Device ID，再调用 `rtDeviceCanAccessPeer(canAccessPeer, deviceId, peerPhyId)`。注意 **`deviceId` 未做同样的转换**，直接作为驱动 Device ID 传入。
- RTS 层 `ApiImpl::DeviceCanAccessPeer` 依次判断：
  1. 芯片是否开放 `RT_FEATURE_DEVICE_P2P`，不支持直接返回 `RT_ERROR_FEATURE_NOT_SUPPORT`；
  2. 运行模式是否为离线（`RT_RUN_MODE_OFFLINE`），离线直接返回 `RT_ERROR_FEATURE_NOT_SUPPORT`；
  3. 当前 Context 是否有效，无效返回 `RT_ERROR_CONTEXT_NULL`；
  4. 通过后才委托驱动（`NpuDriver::DeviceCanAccessPeer`）查询。
- 因此本接口的“不支持”有歧义：真正的“两 Device 不连通”通过 `canAccessPeer=0` 正常返回，而芯片能力缺失、离线或无 Context 会以错误码返回。

## 函数原型

```c
aclError aclrtDeviceCanAccessPeer(int32_t *canAccessPeer, int32_t deviceId, int32_t peerDeviceId);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| canAccessPeer | 输出 | 是否支持数据交互，1 表示支持，0 表示不支持。 |
| deviceId | 输入 | 指定 Device ID，不能与 `peerDeviceId` 相同。范围 `[0, 可用 Device 数量-1]`。 |
| peerDeviceId | 输入 | 指定 peer Device ID，不能与 `deviceId` 相同。范围 `[0, 可用 Device 数量-1]`。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误（rtError_t 符号） | 对外 aclError | 触发点 |
| --- | --- | --- |
| —（ACL 层直接返回） | `ACL_ERROR_INVALID_PARAM`（100000） | `deviceId` 等于 `peerDeviceId` |
| `RT_ERROR_FEATURE_NOT_SUPPORT` | `ACL_ERROR_RT_FEATURE_NOT_SUPPORT`（207000） | 芯片未开放 P2P 特性，或运行在离线模式 |
| `RT_ERROR_CONTEXT_NULL` | `ACL_ERROR_RT_CONTEXT_NULL`（107002） | 当前 Context 无效 |

`peerDeviceId` 反查物理 ID 失败等路径会以内部码经 `ErrorcodeManage::GetRtExtErrCode` 映射后返回；未登记的内部码（不小于 `RT_ERRORCODE_BASE`）统一落到 `ACL_ERROR_RT_INTERNAL_ERROR`（507000）。

## 约束说明

- 仅支持物理机和容器场景，且仅限同一个 PCIe Switch（AI Server 场景可跨 PCIe Switch）、同一物理机/容器、同一进程内的线程间 Device 数据交互；不支持跨进程。
- Atlas 推理系列产品在 Control CPU 开放形态下运行在 Device 的 Control CPU 上时不支持 Device 间数据交互。
- 查询结果为 `canAccessPeer=1` 只是能力探测；实际开启还需调用 [aclrtDeviceEnablePeerAccess](aclrt_device_enable_peer_access.md)，且开启是单向的。
- 产品支持范围不含 Atlas 200I/500 A2 推理产品（`310b`）。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/device/2_device_P2P/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/device/2_device_P2P/main.cpp#L36)：查询 Device 0 访问 Device 1 的能力。
