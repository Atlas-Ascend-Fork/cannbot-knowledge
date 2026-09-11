---
type: API
title: __int2half_rn
description: 遵循CAST_RINT模式，将int32类型数据转换为half类型数据，返回转换后的值。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.type_conversion
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__int2half_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/asc_fp16.h
---

# \_\_int2half\_rn

## 功能说明

遵循CAST\_RINT模式，将int32类型数据转换为half类型数据，返回转换后的值。

## 函数原型

```cpp
inline half __int2half_rn(const int x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

输入遵循CAST\_RINT模式转换成的half类型数据。特殊值如下：

| x值 | 返回值 |
| --- | --- |
| 0 | 0 |
| ±2049 | ±2048 |
| ±2051 | ±2052 |
| ASCRT\_MAX\_NORMAL\_FP16 | ASCRT\_MAX\_NORMAL\_FP16 |
| 65505 | ASCRT\_MAX\_NORMAL\_FP16 |
| -65505 | -ASCRT\_MAX\_NORMAL\_FP16 |
| x≥65520 | inf |
| x≤-65520 | -inf |

## 约束说明

无

## 需要包含的头文件

使用该接口需要包含`simt_api/asc_fp16.h`头文件。

```cpp
#include "simt_api/asc_fp16.h"
```

## 调用示例

- SIMT编程场景：

    ```cpp
    __global__ __launch_bounds__(1024) void kernel__int2half_rn(half* dst, int32_t* x, uint32_t total_length)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        if (idx >= total_length) {
            return;
        }
        dst[idx] = __int2half_rn(x[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void kernel__int2half_rn(__gm__ half* dst, __gm__ int32_t* x, uint32_t total_length)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        if (idx >= total_length) {
            return;
        }
        dst[idx] = __int2half_rn(x[idx]);
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [__int2half_rn_sat](_int2half_rn_sat.md)（`same_topic`）：功能：将int32类型数据按照CAST_RINT模式转换为half类型数据，返回转换后的值。；功能：遵循CAST_RINT模式，将int32类型数据转换为half类型数据，返回转换后的值。。两端共享 int32 到 half 的 CAST_RINT 转换；sat 变体还披露 SIMT 场景无法设置 CTRL、饱和模式不生效，互读可核对所谓饱和入口的实际行为。
<!-- cannbot:related:end -->
