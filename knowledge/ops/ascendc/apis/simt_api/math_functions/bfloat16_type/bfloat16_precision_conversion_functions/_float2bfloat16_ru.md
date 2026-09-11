---
type: API
title: __float2bfloat16_ru
description: 遵循CAST_CEIL模式，将浮点数转换为bfloat16精度，返回转换后的值。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.type_conversion
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__float2bfloat16_ru.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/asc_bf16.h
---

# \_\_float2bfloat16\_ru

## 功能说明

遵循CAST\_CEIL模式，将浮点数转换为bfloat16精度，返回转换后的值。

## 函数原型

```cpp
inline bfloat16_t __float2bfloat16_ru(const float x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

输入遵循CAST\_CEIL模式转换成的bfloat16类型数据。本接口受全局饱和模式影响，特殊值如下：

| x值 | 非饱和模式返回值 | 饱和模式返回值 |
|---|---|---|
| 0 | 0 | 0 |
| -0 | -0 | -0 |
| nan | nan | 0 |
| inf | inf | ASCRT_MAX_NORMAL_BF16 |
| -inf | -inf | -ASCRT_MAX_NORMAL_BF16 |
| ＞ASCRT_MAX_NORMAL_BF16 | inf | ASCRT_MAX_NORMAL_BF16 |
| ＜-ASCRT_MAX_NORMAL_BF16 | -ASCRT_MAX_NORMAL_BF16 | -ASCRT_MAX_NORMAL_BF16 |

## 约束说明

无

## 需要包含的头文件

使用该接口需要包含`simt_api/asc_bf16.h`头文件。

```cpp
#include "simt_api/asc_bf16.h"
```

## 调用示例

-   SIMT编程场景：

    ```cpp
    __global__ __launch_bounds__(1024) void kernel__float2bfloat16_ru(bfloat16_t* dst, float* x)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __float2bfloat16_ru(x[idx]);
    }
    ```

-   SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void kernel__float2bfloat16_ru(__gm__ bfloat16_t* dst, __gm__ float* x)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __float2bfloat16_ru(x[idx]);
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [__float2bfloat16_ru_sat](_float2bfloat16_ru_sat.md)（`same_topic`）：“饱和模式下，将浮点数转换为bfloat16精度，并遵循CAST_CEIL模式，返回转换后的值。”与“遵循CAST_CEIL模式，将浮点数转换为bfloat16精度，返回转换后的值。”是双方正文中的具体合同。两端共享 float 到 bfloat16 的 CAST_CEIL 舍入合同，sat 版本增加饱和处理，互读能避免把边界值行为当成普通向上舍入。
<!-- cannbot:related:end -->
