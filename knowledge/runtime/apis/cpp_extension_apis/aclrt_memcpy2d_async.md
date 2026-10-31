---
type: API
title: aclrtMemcpy2dAsync
description: "C++ 模板向 Stream 下发带源、目的 pitch 的二维复制；Host 锁页内存下异步，非锁页内存下完成后返回。"
tags:
- task.lookup
- topic.data_movement.data_copy
- topic.implementation.api_layer.cpp_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/26_cpp_extension_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt_api.h
  role: header
source_headers:
- include/external/acl/acl_rt_api.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# aclrtMemcpy2dAsync

## 功能说明

实现异步内存复制，主要用于矩阵数据的复制。异步接口。
本接口中的Host内存支持锁页内存（例如通过aclrtMallocHost接口申请的内存）、非锁页内存（通过malloc接口申请的内存）。当Host内存是非锁页内存时，本接口在内存复制任务完成后才返回；当Host内存是锁页内存时，本接口是异步接口，调用接口成功仅表示任务下发成功，不表示任务执行成功，调用本接口后，需调用同步等待接口（例如，aclrtSynchronizeStream）确保内存复制的任务已执行完成。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtMemcpy2dAsync。

## 函数原型

```cpp
template <typename T, typename U>
aclError aclrtMemcpy2dAsync(T *dst, size_t dpitch, const U *src, size_t spitch, size_t width, size_t height, aclrtMemcpyKind kind, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| dst | 输入 | 目的内存地址指针。 |
| dpitch | 输入 | 目的内存中相邻两列向量的地址距离。 |
| src | 输入 | 源内存地址指针。 |
| spitch | 输入 | 源内存中相邻两列向量的地址距离。 |
| width | 输入 | 待复制的数据宽度。<br>width最大设置为5000000，且必须小于或等于dpitch和spitch。 |
| height | 输入 | 待复制的数据高度。<br>height最大设置为5*1024*1024=5242880，否则接口返回失败。 |
| kind | 输入 | 内存复制的类型。类型定义请参见aclrtMemcpyKind。 |
| stream | 输入 | 指定执行内存复制任务的Stream。类型定义请参见aclrtStream。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。


## 约束说明

约束与C接口aclrtMemcpy2dAsync保持一致。
