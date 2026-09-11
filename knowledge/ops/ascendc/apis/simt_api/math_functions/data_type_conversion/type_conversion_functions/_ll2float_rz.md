---
type: API
title: __ll2float_rz
description: 遵循CAST_TRUNC模式，将int64类型数据转换为浮点数，返回转换后的值。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.type_conversion
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__ll2float_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/device_functions.h
---

# \_\_ll2float\_rz

## 功能说明

遵循CAST\_TRUNC模式，将int64类型数据转换为浮点数，返回转换后的值。

## 函数原型

```cpp
inline float __ll2float_rz(const long long int x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

输入遵循CAST\_TRUNC模式转换成的浮点数。特殊值如下：

| x值 | 返回值 |
|---|---|
| 0 | 0 |
| 16777217（2^24+1 ） | ASCRT_TWO_TO_24_F |
| -16777217（-2^24-1） | -ASCRT_TWO_TO_24_F |
| 9223372036854775807（INT64_MAX） | 9.22337149e+18 |
| -9223372036854775808（INT64_MIN） | -9.22337204e+18 |

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
    __global__ __launch_bounds__(1024) void kernel__ll2float_rz(float* dst, int64_t* x)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __ll2float_rz(x[idx]);
    }
    ```

-   SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void kernel__ll2float_rz(__gm__ float* dst, __gm__ int64_t* x)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __ll2float_rz(x[idx]);
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [__ll2float_rd](_ll2float_rd.md)（`same_topic`）：“功能：遵循CAST_TRUNC模式，将int64类型数据转换为浮点数，返回转换后的值。”与“功能：遵循CAST_FLOOR模式，将int64类型数据转换为浮点数，返回转换后的值。”是双方正文中的具体合同。两端都将 int64 转换为浮点数，分别采用向零截断与向下取整，互读能针对负数与非精确表示值选择舍入模式。
<!-- cannbot:related:end -->
