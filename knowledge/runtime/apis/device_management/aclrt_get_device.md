---
type: API
title: aclrtGetDevice
description: 获取当前正在使用的 Device ID；有有效 Context 时取 Context 绑定的用户 Device ID，无 Context 但已 SetDevice 时回退到默认 Device，两者都没有则返回 ACL_ERROR_RT_CONTEXT_NULL。
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
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/api_c_device.cc
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

# aclrtGetDevice

## 功能说明

获取当前正在使用的 Device 的 ID。返回的是**用户 Device ID**（即调用方在 `aclrtSetDevice` 中使用的编号），不是驱动内部 Device ID。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- ACL 层 `aclrtGetDeviceImpl` 先做空指针校验，再调用 `rtGetDevice`，不改变错误数值。
- `ApiImpl::GetDevice` 的取值来源分三档，按优先级判定：
  1. 当前线程有有效 Context（`ContextManage::CheckContextIsValid`）→ 取 `curCtx->UserDeviceId()`；该值若为 `MAX_UINT32_NUM` 哨兵，则由 `curCtx->Device_()->Id_()` 反查用户编号。
  2. Context 无效但已置位"默认 Device"标记（`GetSetDefaultDevIdFlag()`，即本线程调用过 `aclrtSetDevice`）→ 取默认 Device 的驱动 ID 并反查用户编号后返回。
  3. 两者都不满足 → 返回 `RT_ERROR_CONTEXT_NULL`。
- 第 2 档是本接口较易被误判的地方：**即使当前没有有效 Context，只要本线程 SetDevice 过，调用仍会成功**，不会报错。
- RTS 层对 `RT_ERROR_CONTEXT_NULL` 走 `COND_RETURN_WITH_NOLOG` 专用分支，直接返回 `ACL_ERROR_RT_CONTEXT_NULL`，不经通用映射表，也不写入全局错误码。

## 函数原型

```c
aclError aclrtGetDevice(int32_t *deviceId);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| deviceId | 输出 | Device ID 的指针，由接口写入。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误（rtError_t 符号） | 对外 aclError | 触发点 |
| --- | --- | --- |
| —（ACL 层直接返回） | `ACL_ERROR_INVALID_PARAM`（100000） | `deviceId` 为空指针 |
| `RT_ERROR_CONTEXT_NULL` | `ACL_ERROR_RT_CONTEXT_NULL`（107002） | 既无有效 Context，也未在本线程调用过 `aclrtSetDevice` |

用户 Device ID 反查失败等路径会以内部码经 `ErrorcodeManage::GetRtExtErrCode` 映射后返回，未登记的内部码（不小于 `RT_ERRORCODE_BASE`）统一落到 `ACL_ERROR_RT_INTERNAL_ERROR`（507000）。`ACL_ERROR_INVALID_PARAM` 是 ACL 层错误码，不参与 rtError 映射。

## 约束说明

- 文档口径"未提前指定计算设备则返回错误"对应上表第 2 行：需先调用 [aclrtSetDevice](aclrt_set_device.md) 或建立有效 Context。仅当本线程从未 SetDevice 且无有效 Context 时才会失败——其他线程 SetDevice 不会让本线程获得默认 Device。
- 返回的是用户编号，与 `ASCEND_RT_VISIBLE_DEVICES` 的可见集合重排一致；不要把返回值当作驱动 Device ID 直接传给驱动接口。
- 本接口只读当前绑定，不改变线程状态，可与 [aclrtGetDeviceCount](aclrt_get_device_count.md) 配合做设备枚举与校验。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/5_runtime_lifecycle_callbacks/0_reference_counted_plugin_lifecycle/plugin_lifecycle.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/5_runtime_lifecycle_callbacks/0_reference_counted_plugin_lifecycle/plugin_lifecycle.cpp#L106)
- [`6_scenarios/image_processing/0_watershed_image_staging/watershed_image_staging.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/6_scenarios/image_processing/0_watershed_image_staging/watershed_image_staging.cpp#L78)
