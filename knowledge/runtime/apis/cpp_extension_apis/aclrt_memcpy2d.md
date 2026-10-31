---
type: API
title: aclrtMemcpy2d
description: "C++ 模板同步复制二维矩阵区域，分别指定源、目的 pitch 及 width、height，内部调用同名 C 接口。"
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

# aclrtMemcpy2d

## 功能说明

实现同步内存复制，主要用于矩阵数据的复制。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtMemcpy2d。

## 函数原型

```cpp
template <typename T, typename U>
aclError aclrtMemcpy2d(T *dst, size_t dpitch, const U *src, size_t spitch, size_t width, size_t height, aclrtMemcpyKind kind)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| dst | 输入 | 目的内存地址指针。 |
| dpitch | 输入 | 目的内存中相邻两列向量的地址距离。 |
| src | 输入 | 源内存地址指针。 |
| spitch | 输入 | 源内存中相邻两列向量的地址距离。 |
| width | 输入 | 待复制的数据宽度。 |
| height | 输入 | 待复制的数据高度。 |
| kind | 输入 | 内存复制的类型。类型定义请参见aclrtMemcpyKind。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。


## 约束说明

约束与C接口aclrtMemcpy2d保持一致。
