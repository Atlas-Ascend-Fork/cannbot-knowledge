---
type: API
title: Sincosf
description: 获取输入数据的三角函数正弦值和余弦值。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/sincosf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/math_functions.h
---

# sincosf

## 功能说明

获取输入数据的三角函数正弦值和余弦值。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002516816357.png)

## 函数原型

```cpp
inline void sincosf(float x, float *s, float *c)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |
| s | 输出 | UB、Global Memory或栈空间的地址，用于存储输入数据的三角函数正弦值。 |
| c | 输出 | UB、Global Memory或栈空间的地址，用于存储输入数据的三角函数余弦值。 |

## 返回值说明

-   当输入x为inf、-inf、nan时，输出值为nan。

## 约束说明

无

## 需要包含的头文件

使用该接口需要包含`simt_api/math_functions.h`头文件。

```cpp
#include "simt_api/math_functions.h"
```

## 调用示例

- SIMT编程场景：

    ```cpp
    __global__ __launch_bounds__(256) void compute_sincosf(float *sin_result, float *cos_result, const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        sincosf(x[idx], sin_result + idx, cos_result + idx);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(256) inline void compute_sincosf_vf(__gm__ float *sin_result, __gm__ float *cos_result, __gm__ const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        sincosf(x[idx], sin_result + idx, cos_result + idx);
    }

    __global__ __vector__ void run_sincosf(__gm__ float *sin_result, __gm__ float *cos_result, __gm__ const float *x, uint32_t count)
    {
        asc_vf_call<compute_sincosf_vf>(dim3(256), sin_result, cos_result, x, count);
    }
    ```

输入输出示例如下：

```
x：0.25, 0.75, 1.25, 1.75
sin_result: 0.247404 0.6816388 0.9489846 0.983986
cos_result: 0.9689124 0.7316889 0.3153224 -0.1782461
```


<!-- cannbot:related:start -->
## 相关

- [Sincospif](sincospif.md)（`same_topic`）：获取输入数据与π相乘的三角函数正弦值和余弦值；获取输入数据的三角函数正弦值和余弦值。两端一次返回 sin/cos 双结果，区别是 Sincospif 先把输入按 π 缩放而 Sincosf 直接使用弧度；对照可避免调用者重复乘 π 或漏乘 π。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [SimThreadExponential 950 ACLNN 算子知识](../../../../operators/aclnn/math/random/sim_thread_exponential_950.md)（`related`）：算子声明的固定版本源码包含对 `sincosf(...)` 的直接调用（第 323 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/random/random_common/op_kernel/arch35/random_kernel_base.h#L323)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
