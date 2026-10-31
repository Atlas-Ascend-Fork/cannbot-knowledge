---
type: API
title: aclrtSetDevice
description: 为当前线程指定运算 Device 并隐式建立默认 Context；内部按 Device 维护 Primary Context 引用计数，与 aclrtResetDevice 按次数配对，多线程共享同一默认 Context。
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

# aclrtSetDevice

## 功能说明

指定当前线程中用于运算的 Device。成功调用后，当前线程获得该 Device 上可用的默认执行环境（默认 Context 与默认 Stream），后续 Runtime API 可直接使用；不同线程可指定同一 Device，共享同一个默认 Context。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- 每次成功调用对该 Device 的 Primary Context 引用计数加一（`Runtime::PrimaryContextRetain`）；首次调用触发默认 Context 与默认 Stream 的惰性创建，后续调用只复用并加计数。
- 线程绑定写入线程局部存储：`curRef_` 槽位指向 Primary Context 引用，同时清空显式绑定槽位 `curCtx_`（`ApiImpl::SetDevice`）。因此本接口会覆盖线程此前通过 `aclrtSetCurrentContext` 建立的显式绑定；绑定不跨线程继承，每个使用 Runtime API 的线程需各自调用。
- 引用计数是进程级的，与 `aclrtResetDevice` 按次数配对：Set N 次需 Reset N 次，计数归零才真正释放默认 Context 及其资源。

## 函数原型

```c
aclError aclrtSetDevice(int32_t deviceId);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| deviceId | 输入 | Device ID，取值范围 [0, 可见 Device 数)。设置 `ASCEND_RT_VISIBLE_DEVICES` 时按可见集合重排后的用户编号解释。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误（rtError_t 符号） | 触发点 | 调用方处理 |
| --- | --- | --- |
| `RT_ERROR_DEVICE_RETAIN` | Primary Context 获取/初始化失败（devId 越界、TS 配置非法、Device 创建失败等） | 线程绑定未写入，修正后重试 |
| `RT_ERROR_CONTEXT_DEFAULT_STREAM_NULL` | Context 就绪但默认 Stream 缺失 | 此时引用计数已加一且绑定已写入，失败存在半副作用，勿假定完全无状态 |

对外 `aclError` 数值经错误码映射，与内部符号非一一对应；排查以日志中的内部符号为准。

## 约束说明

- 与 `aclrtResetDevice` 配对使用；多次 Set 后普通 Reset 需相同次数才触发释放，`aclrtResetDeviceForce` 则一次清空计数。计数已为零时再 Reset 返回错误。
- 任一线程把计数 Reset 到零会使其他线程的默认 Context 绑定失效，后续调用报无有效 Context 错误；多线程程序建议由单一 owner 统一 Reset。
- 多 TS 平台上一次调用会对该 Device 的每个 TS 槽位分别持有 Primary Context 引用，"一个 Device 一个默认 Context"是单 TS 场景的简化说法。
- 释放后 Runtime 可能保留 Context 对象供下次 SetDevice 复用；"资源已释放"不代表对象内存已销毁，不得缓存旧句柄使用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/0_hello_cann/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/0_hello_cann/main.cpp#L96)
- [`0_quickstart/1_error_handling/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/1_error_handling/main.cpp#L52)
- [`0_quickstart/3_cross_version/0_runtime_compatibility/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/3_cross_version/0_runtime_compatibility/main.cpp#L85)

## 配套 API 与常见组合

- [aclrtResetDevice](aclrt_reset_device.md)——与本接口按次数配对，Set N 次需 Reset N 次，计数归零才释放默认 Context
- [aclrtResetDeviceForce](aclrt_reset_device_force.md)——需要一次清空引用计数强制释放时，用强制变体替代按计数 Reset
- [aclrtGetDevice](aclrt_get_device.md)——查询当前线程已绑定的 Device ID；该线程绑定不跨线程继承
