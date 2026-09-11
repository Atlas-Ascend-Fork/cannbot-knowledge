---
type: API
title: __float2bfloat16_rn_sat
description: 饱和模式下，将浮点数转换为bfloat16精度，并遵循CAST_RINT模式，返回转换后的值。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.type_conversion
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__float2bfloat16_rn_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/asc_bf16.h
---

# \_\_float2bfloat16\_rn\_sat

## 功能说明

饱和模式下，将浮点数转换为bfloat16精度，并遵循CAST\_RINT模式，返回转换后的值。

## 函数原型

```cpp
inline bfloat16_t __float2bfloat16_rn_sat(const float x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

饱和模式下将输入遵循CAST\_RINT模式转换成的bfloat16类型数据。特殊值如下：

| x值 | 非饱和模式返回值 | 饱和模式返回值 |
|---|---|---|
| +0 | 0 | 0 |
| -0 | -0 | -0 |
| nan | nan | 0 |
| inf | inf | ASCRT_MAX_NORMAL_BF16 |
| -inf | -inf | -ASCRT_MAX_NORMAL_BF16 |
| ASCRT_MAX_NORMAL_F | inf | ASCRT_MAX_NORMAL_BF16 |
| -ASCRT_MAX_NORMAL_F | -inf | -ASCRT_MAX_NORMAL_BF16 |

## 约束说明

使用此接口前需将CTRL\[60\]寄存器设置为0，否则饱和模式不生效。设置方式请参见[控制饱和行为的方式](../../data_type_conversion/overview.md#section1194916101549)。

SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。

## 需要包含的头文件

使用该接口需要包含`simt_api/asc_bf16.h`头文件。

```cpp
#include "simt_api/asc_bf16.h"
```

## 调用示例

-   SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void kernel__float2bfloat16_rn_sat(__gm__ bfloat16_t* dst, __gm__ float* x)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __float2bfloat16_rn_sat(x[idx]);
    }
    ```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [CircularPad2dBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/circular_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `__float2bfloat16_rn_sat(...)` 的直接调用（第 107 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/arch35/pad_v3_grad_circular_simt.h#L107)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
