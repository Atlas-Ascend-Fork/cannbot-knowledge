---
type: API
title: aclrtDeviceSetLimit
description: 设置当前进程的 Device 资源限制（SIMT 栈空间、Printf 维测空间等）；ACL 层校验 limit 在 [0,4] 且 value 不超过 UINT32_MAX，内部固定用 Device0 设置，不支持的资源类型返回 ACL_ERROR_RT_FEATURE_NOT_SUPPORT。
tags:
- task.lookup
- topic.implementation
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
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/impl/api_impl_david.cc
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-28T07:09:42Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- a3
- a2
---

# aclrtDeviceSetLimit

## 功能说明

设置当前进程的 Device 资源限制，例如 SIMT 算子栈空间大小、SIMT Printf 维测空间大小等。配置作用于当前进程，所有 Device 共用同一套值。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- ACL 层 `aclrtDeviceSetLimitImpl` 先把 `aclrtDeviceLimit` 经 `AclLimitToRtLimit` 映射为 `rtLimitType_t`：`limit` 索引不在 `[0,4]` 时映射为 `RT_LIMIT_TYPE_RESERVED`，接口返回 `ACL_ERROR_INVALID_PARAM`（提示期望 `[0, 4]`）；`value > UINT32_MAX` 同样返回 `ACL_ERROR_INVALID_PARAM`。校验通过后固定以 `devId=0` 调用 `rtDeviceSetLimit(0, rtType, value)`。
- RTS 包装 `rtDeviceSetLimit` 对 `RT_ERROR_FEATURE_NOT_SUPPORT` 走专用分支，直接返回 `ACL_ERROR_RT_FEATURE_NOT_SUPPORT`（207000），不经通用映射表。
- `ApiImpl::DeviceSetLimit` 忽略传入的 `devId`。标准 SoC 实现把 `SIMT_PRINTF_FIFO_SIZE`、`SIMT_STACK_SIZE`、`SIMT_DVG_WARP_STACK_SIZE` 一律判为本平台不支持并返回 `RT_ERROR_FEATURE_NOT_SUPPORT`；`STACK_SIZE` 写 `Runtime::SetDeviceCustomerStackSize`，`SIMD_PRINTF_FIFO_SIZE_PER_CORE` 写 `SetSimdPrintFifoSize`，其余类型经当前 Context 的 `DevSetLimit`。Ascend 950 走 `ApiImplDavid::DeviceSetLimit`，支持 SIMT 栈/Printf 限制。

## 函数原型

```c
aclError aclrtDeviceSetLimit(aclrtDeviceLimit limit, size_t value);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| limit | 输入 | 资源类型，取值见 `aclrtDeviceLimit`，范围 `[0,4]`。 |
| value | 输入 | 资源限制的大小，单位 Byte；取值不得超过 `UINT32_MAX`，具体含义随 `limit` 不同。 |

### aclrtDeviceLimit 取值

| 值 | 枚举 | 说明 |
| --- | --- | --- |
| 0 | ACL_RT_DEV_LIMIT_SIMT_STACK_SIZE | SIMT 算子栈空间大小 |
| 1 | ACL_RT_DEV_LIMIT_SIMT_DVG_WARP_STACK_SIZE | SIMT DVG warp 栈空间大小 |
| 2 | ACL_RT_DEV_LIMIT_SIMD_STACK_SIZE | SIMD 栈空间大小 |
| 3 | ACL_RT_DEV_LIMIT_SIMD_PRINTF_FIFO_SIZE_PER_CORE | 每核 SIMD Printf FIFO 大小 |
| 4 | ACL_RT_DEV_LIMIT_SIMT_PRINTF_FIFO_SIZE | SIMT Printf FIFO 大小 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 / 返回 | 对外 aclError | 触发点 |
| --- | --- | --- |
| —（ACL 层直接返回） | `ACL_ERROR_INVALID_PARAM`（100000） | `limit` 不在 `[0,4]`，或 `value` 超过 `UINT32_MAX` |
| `RT_ERROR_FEATURE_NOT_SUPPORT` | `ACL_ERROR_RT_FEATURE_NOT_SUPPORT`（207000） | 目标产品/实现路径不支持该资源类型 |
| 驱动/内部码 | 经 `ErrorcodeManage::GetRtExtErrCode` 映射 | Context 无效或驱动设置失败 |

未登记的内部码（不小于 `RT_ERRORCODE_BASE`）统一落到 `ACL_ERROR_RT_INTERNAL_ERROR`（507000）。

## 约束说明

- 建议在 `aclInit` 之后、`aclrtSetDevice` 之前调用；若涉及多次 `aclrtSetDevice`，需先用 `aclrtResetDevice` 让引用计数归零，再调用本接口设置，之后重新 `aclrtSetDevice` 才生效。
- 本接口内部固定使用 Device 0；设置了 `ASCEND_RT_VISIBLE_DEVICES` 时必须包含 Device0，否则配置失败。可用 [aclrtGetDeviceInfo](aclrt_get_device_info.md) 查询 `ACL_DEV_ATTR_IS_VIRTUAL` 等属性辅助判断环境。
- 本接口与 `aclInit` 均可配置资源限制，后配置覆盖先配置；配置作用于当前进程，所有 Device 共用，无法按 Device 区分。
- 产品支持为 Ascend 950 / A3 / A2；Atlas 200I/500 A2 推理产品（`310b`）、Atlas 推理系列产品（`310p`）与早期 Ascend 910 不支持。A3/A2 对 SIMT 类资源类型会返回 `ACL_ERROR_RT_FEATURE_NOT_SUPPORT`。
