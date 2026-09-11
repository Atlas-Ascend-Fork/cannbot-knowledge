---
type: API
title: __hmin
description: 获取两个输入数据中的最小值。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.type_conversion
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_compare_functions/__hmin.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/asc_bf16.h
---

# \_\_hmin

## 功能说明

获取两个输入数据中的最小值。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002545900874.png)

## 函数原型

```cpp
inline bfloat16_t __hmin(bfloat16_t x, bfloat16_t y)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |
| y | 输入 | 源操作数。 |

## 返回值说明

两个输入数据中的最小值。本接口不受全局饱和模式影响，特殊值如下：

| x值 | y值 | 返回值 |
| --- | --- | --- |
| +0 | -0 | -0 |
| -0 | +0 | -0 |
| nan | 非特殊数值（非nan，inf，-inf） | y值 |
| 非特殊数值（非nan，inf，-inf） | nan | x值 |
| nan | nan | nan |
| x，y任意一个为-inf | — | -inf |
| inf | 非特殊数值（非nan，inf，-inf） | y |
| 非特殊数值（非nan，inf，-inf） | inf | x |

## 约束说明

无

## 需要包含的头文件

使用bfloat16\_t类型接口需要包含`simt_api/asc_bf16.h`头文件。

```cpp
#include "simt_api/asc_bf16.h"
```

## 调用示例

- SIMT编程场景：

    ```cpp
    __global__ __launch_bounds__(1024) void kernel_min(bfloat16_t* dst, bfloat16_t* x, bfloat16_t* y, uint32_t total_length)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        if (idx >= total_length) {
            return;
        }
        dst[idx] = __hmin(x[idx], y[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void kernel_min(__gm__ bfloat16_t* dst, __gm__ bfloat16_t* x, __gm__ bfloat16_t* y, uint32_t total_length)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        if (idx >= total_length) {
            return;
        }
        dst[idx] = __hmin(x[idx], y[idx]);
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [__hmin_nan](_hmin_nan.md)（`same_topic`）：获取两个输入数据中的最小值。；获取两个输入数据中的最小值。任一输入为nan时，结果为nan。。两接口计算相同 bfloat16 最小值，候选显式提供 NaN 传播版本，适合按异常值契约选择。
<!-- cannbot:related:end -->
