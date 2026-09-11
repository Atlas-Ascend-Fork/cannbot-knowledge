---
type: API
title: __umulhi
description: 获取输入uint32类型数据x和y乘积的高32位。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.arithmetic
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__umulhi.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/device_functions.h
---

# \_\_umulhi

## 功能说明

获取输入uint32类型数据x和y乘积的高32位。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002531050526.png)

## 函数原型

```cpp
unsigned int __umulhi(unsigned int x, unsigned int y)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数，乘数。 |
| y | 输入 | 源操作数，乘数。 |

## 返回值说明

输入uint32类型数据x和y乘积的高32位。

## 约束说明

无

## 需要包含的头文件

使用该接口需要包含`simt_api/device_functions.h`头文件。

```cpp
#include "simt_api/device_functions.h"
```

## 调用示例

-   SIMT编程场景：

    ```cpp
    __global__ __launch_bounds__(1024) void KernelUmulhi(unsigned int* dst, unsigned int* x, unsigned int* y)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __umulhi(x[idx], y[idx]);
    }
    ```

-   SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void KernelUmulhi(__gm__ unsigned int* dst, __gm__ unsigned int* x, __gm__ unsigned int* y)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __umulhi(x[idx], y[idx]);
    }
    ```


- [Cat 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/cat_950.md)
- [GatherNd 950 ACLNN 算子知识](../../../../operators/aclnn/nn/index/gather_nd_950.md)
- [Eye 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/eye_950.md)
- [InplaceScatterUpdate 950 ACLNN 算子知识](../../../../operators/aclnn/nn/index/inplace_scatter_update_950.md)
- [OneHot 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/one_hot_950.md)
