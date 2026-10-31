---
type: API
title: aclrtDeviceGetP2PAtomicCapabilities
description: 查询同一 AI Server 内两个 Device 之间支持的原子操作详情；实现先清零 capabilities 再按 operations 索引填充，仅当两 Device 拓扑为 HCCS/SIO/HCCS_SW/UB 时视为支持，拓扑查询失败会直接报错。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.atomic
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/04_device_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/25-02_Enumerations.md
  role: supporting
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/device.cpp
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
- '310b'
- '310p'
- '910'
---

# aclrtDeviceGetP2PAtomicCapabilities

## 功能说明

查询同一 AI Server 内两个 Device 之间支持的原子操作详情。AI Server 通常指多个 Device 组成的服务器形态。`capabilities` 是位掩码数组，长度与 `count` 一致。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- ACL 层 `aclrtDeviceGetP2PAtomicCapabilitiesImpl` 只把 `operations` 由 `aclrtAtomicOperation*` 转成 `rtAtomicOperation*`，**不校验指针与 count**。
- `ApiImpl::GetP2PAtomicCapabilities` 流程：
  1. `GetAtomicDevProperties` 先把 `capabilities[0..count)` 全部置 0，再按芯片取 `DevProperties`；
  2. `CheckP2PAtomicSupport(srcDeviceId, dstDeviceId, supported)` 用驱动 `GetPairDevicesInfo(..., DEVS_INFO_TYPE_TOPOLOGY, ...)` 查询两 Device 拓扑：仅当拓扑为 `TOPOLOGY_HCCS`、`TOPOLOGY_SIO`、`TOPOLOGY_HCCS_SW` 或 `TOPOLOGY_UB` 时 `supported=true`；
  3. `supported` 为真时 `FillAtomicCapabilities` 以 `operations[i]` 为下标从 `prop.p2pAtomicCapabilities` 取值写入，越界操作对应元素保持 0。
- 与 [aclrtDeviceGetHostAtomicCapabilities](aclrt_device_get_host_atomic_capabilities.md) 的关键差异：Host 版本在驱动不支持拓扑查询时**吞掉错误**并返回全 0，而 P2P 版本若 `GetPairDevicesInfo` 失败会**直接返回该错误**。

## 函数原型

```c
aclError aclrtDeviceGetP2PAtomicCapabilities(uint32_t *capabilities, const aclrtAtomicOperation *operations,
                                            const uint32_t count, int32_t srcDeviceId, int32_t dstDeviceId);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| capabilities | 输出 | 原子操作支持能力数组，长度须与 `count` 一致；位定义见 `aclrtAtomicOperationCapability`。 |
| operations | 输入 | 待查询的原子操作数组，长度须与 `count` 一致；类型见 `aclrtAtomicOperation`。 |
| count | 输入 | 待查询的原子操作数量，必须与两个数组长度一致，否则可能造成未定义行为。 |
| srcDeviceId | 输入 | 源 Device ID，范围 `[0, 可用 Device 数量-1]`。 |
| dstDeviceId | 输入 | 目的 Device ID，范围 `[0, 可用 Device 数量-1]`。 |

`aclrtAtomicOperationCapability` 位定义与 `aclrtAtomicOperation` 取值见 [aclrtDeviceGetHostAtomicCapabilities](aclrt_device_get_host_atomic_capabilities.md#aclrtatomicoperationcapability-位定义)。

## 返回值说明

返回 0 表示成功，其他值表示失败。实现中的主要失败来源：

| 内部错误 / 返回 | 对外 aclError | 触发点 |
| --- | --- | --- |
| `RT_ERROR_INVALID_VALUE` | `ACL_ERROR_RT_PARAM_INVALID`（107000） | 取 `DevProperties` 失败 |
| 驱动内部码 | 经 `ErrorcodeManage::GetRtExtErrCode` 映射 | `GetPairDevicesInfo` 查询两 Device 拓扑失败 |

未登记的内部码（不小于 `RT_ERRORCODE_BASE`）统一落到 `ACL_ERROR_RT_INTERNAL_ERROR`（507000）。

## 约束说明

- 仅查询同一 AI Server（同 HCCS/SIO/HCCS_SW/UB 拓扑）内两 Device 间的能力；拓扑不满足时返回成功但 `capabilities` 全 0。
- 拓扑查询失败会直接返回错误，不能仅凭“返回成功但全 0”与“返回错误”两种结果混用判断；需要区分“不支持”与“查询失败”时，应分别处理返回码与数组。
- 查询结果反映的是两 Device 之间的原子能力，与两 Device 是否已通过 [aclrtDeviceEnablePeerAccess](aclrt_device_enable_peer_access.md) 开启 P2P 数据交互相互独立。
- `count` 必须与实际数组长度一致，数组容量由调用方保证。
- 产品支持为 Ascend 950 / A3 / A2 / 310b / 310p / 早期 910；IPV350 不支持。
