---
type: API
title: __half2bfloat16_rna
description: 遵循CAST_ROUND模式，将half类型数据转换为bfloat16类型，返回转换后的值。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.type_conversion
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__half2bfloat16_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/asc_bf16.h
---

# \_\_half2bfloat16\_rna

## 功能说明

遵循CAST\_ROUND模式，将half类型数据转换为bfloat16类型，返回转换后的值。

## 函数原型

```cpp
inline bfloat16_t __half2bfloat16_rna(const half x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

输入遵循CAST\_ROUND模式转换成的bfloat16类型数据。本接口受全局饱和模式影响，特殊值如下：

| x值 | 非饱和模式返回值 | 饱和模式返回值 |
|---|---|---|
| ±0 | ±0 | ±0 |
| nan | nan | 0 |
| inf | inf | ASCRT_MAX_NORMAL_BF16 |
| -inf | -inf | -ASCRT_MAX_NORMAL_BF16 |

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
    __global__ __launch_bounds__(1024) void kernel__half2bfloat16_rna(bfloat16_t* dst, half* x)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __half2bfloat16_rna(x[idx]);
    }
    ```

-   SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void kernel__half2bfloat16_rna(__gm__ bfloat16_t* dst, __gm__ half* x)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __half2bfloat16_rna(x[idx]);
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [__half2bfloat16_rn](_half2bfloat16_rn.md)（`same_topic`）：遵循CAST_RINT模式，将half类型数据转换为bfloat16类型，返回转换后的值。；遵循CAST_ROUND模式，将half类型数据转换为bfloat16类型，返回转换后的值。。两端具有相同 half 到 bfloat16 转换合同，只在 CAST_RINT 与 CAST_ROUND 舍入规则上分流，互读可按数值舍入要求选择入口。
<!-- cannbot:related:end -->
