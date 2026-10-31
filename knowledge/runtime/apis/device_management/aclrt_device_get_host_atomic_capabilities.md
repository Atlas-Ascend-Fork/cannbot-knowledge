---
type: API
title: aclrtDeviceGetHostAtomicCapabilities
description: 查询指定 Device 与 Host 之间支持的原子操作详情；capabilities 为位掩码数组，实现先把数组清零再按 operations 索引填充，不支持（拓扑非 UB 或驱动不支持查询）时返回成功但数组保持全 0。
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

# aclrtDeviceGetHostAtomicCapabilities

## 功能说明

查询指定 Device 与 Host 之间支持的原子操作详情。`capabilities` 是位掩码数组，长度与 `count` 一致；每个元素按 `operations[i]` 对应一种原子操作，掩码的每一位表示对不同数据类型的支持情况（1 支持 / 0 不支持）。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- ACL 层 `aclrtDeviceGetHostAtomicCapabilitiesImpl` 只做 `reinterpret_cast` 把 `aclrtAtomicOperation*` 转成 `rtAtomicOperation*`，**不校验指针与 count**。
- `ApiImpl::GetHostAtomicCapabilities` 流程：
  1. `GetAtomicDevProperties` 先把 `capabilities[0..count)` 全部置 0，再按芯片取 `DevProperties`；
  2. `CheckHostAtomicSupport(deviceId, supported)` 查驱动 `MODULE_TYPE_SYSTEM` / `INFO_TYPE_HD_CONNECT_TYPE`：若驱动返回 `RT_ERROR_DRV_INPUT`（A2/A3 部分驱动版本不支持查询拓扑），视为不支持且仍返回成功；若连接类型不是 `HOST_DEVICE_CONNECT_TYPE_UB`，也视为不支持；
  3. 仅当 `supported` 为真时，`FillAtomicCapabilities` 用 `operations[i]` 作为下标从 `prop.hostAtomicCapabilities` 取值写入；`operations[i]` 超出有效范围时对应元素保持 0。
- 因此“返回 0 且 `capabilities` 全为 0”通常表示该 Device 与 Host 之间不支持对应原子操作，而不是查询失败。

## 函数原型

```c
aclError aclrtDeviceGetHostAtomicCapabilities(
    uint32_t *capabilities, const aclrtAtomicOperation *operations, const uint32_t count, int32_t deviceId);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| capabilities | 输出 | 原子操作支持能力数组，长度须与 `count` 一致；每个元素是位掩码，位定义见 `aclrtAtomicOperationCapability`。 |
| operations | 输入 | 待查询的原子操作数组，长度须与 `count` 一致；类型见 `aclrtAtomicOperation`。 |
| count | 输入 | 待查询的原子操作数量，必须与两个数组长度一致，否则可能造成未定义行为。 |
| deviceId | 输入 | Device ID，范围 `[0, 可用 Device 数量-1]`。 |

### aclrtAtomicOperationCapability 位定义

| 位 | 枚举 | 含义 |
| --- | --- | --- |
| 1<<0 | ACL_RT_ATOMIC_CAPABILITY_SIGNED | 有符号整数 |
| 1<<1 | ACL_RT_ATOMIC_CAPABILITY_UNSIGNED | 无符号整数 |
| 1<<2 | ACL_RT_ATOMIC_CAPABILITY_REDUCTION | 规约（`...REDUCATION` 为同值废弃别名） |
| 1<<3 | ACL_RT_ATOMIC_CAPABILITY_SCALAR8 | 8 位标量 |
| 1<<4 | ACL_RT_ATOMIC_CAPABILITY_SCALAR16 | 16 位标量 |
| 1<<5 | ACL_RT_ATOMIC_CAPABILITY_SCALAR32 | 32 位标量 |
| 1<<6 | ACL_RT_ATOMIC_CAPABILITY_SCALAR64 | 64 位标量 |
| 1<<7 | ACL_RT_ATOMIC_CAPABILITY_SCALAR128 | 128 位标量 |
| 1<<8 | ACL_RT_ATOMIC_CAPABILITY_VECTOR32X4 | 向量 |

`aclrtAtomicOperation` 覆盖整数（Add/Min/Max/Increment/Decrement/And/Or/Xor/Exchange/Cas，0–9）、浮点（Add/Min/Max，10–12）、DMA（Add/Min/Max，30–32）与 SIMD 标量（Add/Min/Max/Cas/Exch，40–44）等操作。

## 返回值说明

返回 0 表示成功，其他值表示失败。实现中的主要失败来源是取 `DevProperties` 失败（内部映射为 `RT_ERROR_INVALID_VALUE` → `ACL_ERROR_RT_PARAM_INVALID`，107000）以及驱动拓扑查询失败；未登记的内部码（不小于 `RT_ERRORCODE_BASE`）统一落到 `ACL_ERROR_RT_INTERNAL_ERROR`（507000）。

## 约束说明

- Device 与 Host 之间是否支持的判定依据是连接拓扑是否为 UB；不满足时接口返回成功但 `capabilities` 全 0。
- `operations[i]` 只作为设备能力表的下标使用，越界或无效操作不会报错，对应元素保持 0。
- `count` 必须与实际数组长度一致，否则可能越界读写；数组容量由调用方保证。
- 产品支持为 Ascend 950 / A3 / A2 / 310b / 310p / 早期 910；IPV350 不支持。
