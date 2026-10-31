---
type: API
title: aclrtDeviceGetLimit
description: 获取当前进程的 Device 资源限制；ACL 层要求 value 非空且 limit 在 [0,4]，查询的是进程内瞬时配置（不一定等于已生效值），不支持的资源类型返回 ACL_ERROR_RT_FEATURE_NOT_SUPPORT。
tags:
- task.lookup
- topic.implementation.resource_query
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

# aclrtDeviceGetLimit

## 功能说明

获取当前进程的 Device 资源限制。查询的是进程内的**瞬时配置值**，不保证等于已生效值，也不保证多线程并发安全。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- ACL 层 `aclrtDeviceGetLimitImpl` 先校验 `value` 非空（否则 `ACL_ERROR_INVALID_PARAM`），再把 `aclrtDeviceLimit` 经 `AclLimitToRtLimit` 映射：`limit` 不在 `[0,4]` 时返回 `ACL_ERROR_INVALID_PARAM`（提示期望 `[0, 4]`）。随后调用 `rtDeviceGetLimit(rtType, &rtValue)` 并写回 `*value`。
- RTS 包装 `rtDeviceGetLimit` 对 `RT_ERROR_FEATURE_NOT_SUPPORT` 走专用分支，直接返回 `ACL_ERROR_RT_FEATURE_NOT_SUPPORT`（207000）。
- `ApiImpl::DeviceGetLimit` 在标准 SoC 实现中把 SIMT 相关的 `SIMT_PRINTF_FIFO_SIZE` / `SIMT_STACK_SIZE` / `SIMT_DVG_WARP_STACK_SIZE` 判为不支持并返回 `RT_ERROR_FEATURE_NOT_SUPPORT`；未识别类型记警告并按 0 返回。Ascend 950 走 `ApiImplDavid::DeviceGetLimit`，支持 SIMT 栈/Printf 限制并可返回设置值。

## 函数原型

```c
aclError aclrtDeviceGetLimit(aclrtDeviceLimit limit, size_t *value);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| limit | 输入 | 资源类型，取值见 `aclrtDeviceLimit`，范围 `[0,4]`。 |
| value | 输出 | 资源限制的大小，单位 Byte，不能为 `nullptr`。 |

`aclrtDeviceLimit` 取值与含义见 [aclrtDeviceSetLimit](aclrt_device_set_limit.md#aclrtdevicelimit-取值)。

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 / 返回 | 对外 aclError | 触发点 |
| --- | --- | --- |
| —（ACL 层直接返回） | `ACL_ERROR_INVALID_PARAM`（100000） | `value` 为空指针，或 `limit` 不在 `[0,4]` |
| `RT_ERROR_FEATURE_NOT_SUPPORT` | `ACL_ERROR_RT_FEATURE_NOT_SUPPORT`（207000） | 目标产品/实现路径不支持该资源类型 |
| 驱动/内部码 | 经 `ErrorcodeManage::GetRtExtErrCode` 映射 | 内部查询失败 |

未登记的内部码（不小于 `RT_ERRORCODE_BASE`）统一落到 `ACL_ERROR_RT_INTERNAL_ERROR`（507000）。

## 约束说明

- 通过 [aclrtDeviceSetLimit](aclrt_device_set_limit.md) 配置的限制作用于当前进程、所有 Device 共用，任意 Device 查询返回相同值。
- 查询值是瞬时配置：先 `SetLimit(A)` 再 `SetDevice` 使其生效，此时查询得到 A；之后 `SetLimit(B)` 但未重新 `SetDevice`，查询得到 B，而实际生效值仍是 A。
- Ascend 950 上查询 `ACL_RT_DEV_LIMIT_SIMT_STACK_SIZE` 返回对齐后 ×32 的值（如设置 256 返回 8192），`ACL_RT_DEV_LIMIT_SIMT_DVG_WARP_STACK_SIZE` 返回对齐值（不乘线程数）。
- A3/A2 查询 SIMT 相关资源类型返回 `ACL_ERROR_RT_FEATURE_NOT_SUPPORT`；产品支持为 Ascend 950 / A3 / A2，`310b`/`310p`/早期 `910` 不支持。
