---
type: API
title: aclrtGetDeviceCount
description: 获取可用 Device 数量；未设置 ASCEND_RT_VISIBLE_DEVICES 时直接向驱动查询，设置后改用可见集合解析结果，环境变量非法（重复、非升序、越界）时返回设备数查询失败错误。
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

# aclrtGetDeviceCount

## 功能说明

获取当前进程可用的 Device 数量。返回的是**可见 Device 数量**：设置了 `ASCEND_RT_VISIBLE_DEVICES` 时，是该环境变量筛选后的数量，而不是机器上的物理卡数。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- ACL 层 `aclrtGetDeviceCountImpl` 先做空指针校验，再调用 `rtGetDeviceCount`。调用处把 `uint32_t*` 以 `reinterpret_cast<int32_t*>` 传入 RTS 层，RTS 侧按 `int32_t*` 写入——在数量不超过 `INT32_MAX` 的前提下二者表示一致，这是实现层的类型约定，不是接口语义。
- `ApiImpl::GetDeviceCount` 按 `isSetVisibleDev` 分两条路径：
  - **未设置** `ASCEND_RT_VISIBLE_DEVICES`：直接委托驱动 `FacadeDriver::GetDeviceCount`，结果由驱动决定。
  - **已设置**：不再问驱动，改用 Runtime 在初始化时解析环境变量得到的 `userDeviceCnt`，并对解析结果做校验。
- 校验失败时按三类原因分别报 EE2002 外部提示，并统一返回 `RT_ERROR_DRV_NO_DEVICE`：可见集合含重复项、未按升序配置、存在超出 `[0, deviceCnt)` 的编号。
- 因此本接口的错误可能来自**环境变量配置错误**，而不只是硬件或驱动问题。

## 函数原型

```c
aclError aclrtGetDeviceCount(uint32_t *count);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| count | 输出 | Device 数量的指针，由接口写入。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误（rtError_t 符号） | 对外 aclError | 触发点 |
| --- | --- | --- |
| —（ACL 层直接返回） | `ACL_ERROR_INVALID_PARAM`（100000） | `count` 为空指针 |
| `RT_ERROR_DRV_NO_DEVICE` | 按其 `GetRtExtErrCode` 映射结果 | `ASCEND_RT_VISIBLE_DEVICES` 含重复项、非升序或编号越界；驱动侧无可用 Device |

未登记的内部码（不小于 `RT_ERRORCODE_BASE`）统一落到 `ACL_ERROR_RT_INTERNAL_ERROR`（507000）。`ACL_ERROR_INVALID_PARAM` 是 ACL 层错误码，不参与 rtError 映射。

## 约束说明

- 结果受 `ASCEND_RT_VISIBLE_DEVICES` 影响，**不是物理卡数**；配置了可见集合时，Device ID 的取值范围是 `[0, 返回的数量)`，而不是物理编号。
- 该环境变量在进程内解析一次；运行中修改不会让本接口重新解析。
- 典型用法是先取数量，再用 [aclrtSetDevice](aclrt_set_device.md) 在 `[0, count)` 内选择 Device；也可以结合 [aclrtGetDevice](aclrt_get_device.md) 校验当前绑定。
- 调用本接口不需要先 SetDevice，也不要求已建立 Context。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/device/1_device_multi_thread/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/device/1_device_multi_thread/main.cpp#L37)
- [`1_basic_features/device/2_device_P2P/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/device/2_device_P2P/main.cpp#L25)
- [`2_advanced_features/ipcevent/1_ipcevent_multi_device/precheck.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/ipcevent/1_ipcevent_multi_device/precheck.cpp#L30)
