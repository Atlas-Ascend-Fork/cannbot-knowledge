---
type: API
title: __uint2half_rn_sat
description: 将uint32类型数据转换为half类型数据，并遵循CAST_RINT模式，返回转换后的值。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.type_conversion
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__uint2half_rn_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/asc_fp16.h
---

# \_\_uint2half\_rn\_sat

## 功能说明

将uint32类型数据转换为half类型数据，并遵循CAST\_RINT模式，返回转换后的值。

## 函数原型

```cpp
inline half __uint2half_rn_sat(const unsigned int x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

遵循CAST\_RINT模式，将输入uint32数据转换成的half数据。特殊值如下：

| x值 | 返回值 |
| --- | --- |
| 0 | 0 |
| x>ASCRT\_MAX\_NORMAL\_FP16 | ASCRT\_MAX\_NORMAL\_FP16 |

## 约束说明

SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。

## 需要包含的头文件

使用该接口需要包含`simt_api/asc_fp16.h`头文件。

```cpp
#include "simt_api/asc_fp16.h"
```

## 调用示例

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void kernel__uint2half_rn_sat(__gm__ half* dst, __gm__ uint32_t* x, uint32_t total_length)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        if (idx >= total_length) {
            return;
        }
        dst[idx] = __uint2half_rn_sat(x[idx]);
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [__uint2half_rn](_uint2half_rn.md)（`same_topic`）：约束：SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。需包含头文件 simt_api/asc_fp16.h。；功能：遵循CAST_RINT模式，将uint32类型数据转换为half类型数据，返回转换后的值。。带 sat 名称的接口在 SIMT 场景明确说明饱和模式不生效，而非 sat 接口执行同样的 uint32→half CAST_RINT 转换，因此当前平台下二者的有效转换核心一致。
<!-- cannbot:related:end -->
