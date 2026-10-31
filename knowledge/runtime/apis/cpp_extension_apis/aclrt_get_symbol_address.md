---
type: API
title: aclrtGetSymbolAddress
description: "C++ 模板按 __gm__ 变量名获取 Device 地址，用于 Ascend C 混合编译；地址仅在当前 Device 有效。"
tags:
- task.lookup
- topic.implementation.resource_query
- topic.memory
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
- a3
- a2
- '310p'
---

# aclrtGetSymbolAddress

## 功能说明

获取Device变量的地址。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtGetSymbolAddress。

## 函数原型

```cpp
template <typename T>
aclError aclrtGetSymbolAddress(const T &symbol, void **devPtr)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| symbol | 输入 | Device变量名。此处传入`__gm__`声明的变量名。 |
| devPtr | 输出 | Device变量的内存地址指针。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。


## 约束说明

- 本接口仅适用于 C++ 程序。
- 本接口仅适用于Ascend C语言开发自定义算子并基于毕昇编译器进行Host和Device代码混合编译的场景。
- Device变量地址仅在当前Device有效，切换Device后需重新获取地址。
- 仅支持AI Core算子中的Device变量，具体约束如下：
    - 支持在main函数所在文件中定义的Device变量（如 `__gm__ float convWeights`）。
    - 支持通过extern关键字跨文件引用Device变量。例如，在文件A中定义`__gm__ float convWeights`，文件B中可通过`extern __gm__ float convWeights`声明并引用该变量。需要满足编译要求：使用毕昇编译器的-dc模式，将多个源文件编译为单个算子二进制文件。
    - 支持基础数据类型、函数指针、结构体及数组，不支持class类型。注意：函数指针只支持指向纯Scalar的函数，不能有效区分Cube和Vector的函数逻辑。
