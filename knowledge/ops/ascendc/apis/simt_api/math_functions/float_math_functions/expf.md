---
type: API
title: 数学函数expf
description: 根据输入x，获取e的x次方的计算结果。 !
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/expf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/math_functions.h
---

# expf

## 功能说明

根据输入x，获取e的x次方的计算结果。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002516816333.png)

## 函数原型

```cpp
inline float expf(float x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数，数据类型为float。 |

## 返回值说明

e的x次方。

-   当x为inf时，返回值为inf。
-   当x为-inf时，返回值为0。
-   当x为nan时，返回值为nan。

## 约束说明

本接口受编译选项[--cce-use-fast-math](../../../../guides/programming_guide/compilation_and_execution/operator_compilation/ai_core_operator_compilation.md#常用的编译选项)的影响。
-   --cce-use-fast-math=true：开启快速计算模式，不支持Subnormal场景，处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。
-   --cce-use-fast-math=false：支持Subnormal场景。

## 需要包含的头文件

使用该接口需要包含`simt_api/math_functions.h`头文件。

```cpp
#include "simt_api/math_functions.h"
```

## 调用示例

- SIMT编程场景：

    ```cpp
    __global__ __launch_bounds__(256) void compute_expf(float *result, const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = expf(x[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(256) inline void compute_expf_vf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = expf(x[idx]);
    }

    __global__ __vector__ void run_expf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        asc_vf_call<compute_expf_vf>(dim3(256), result, x, count);
    }
    ```

输入输出示例如下：

```
x：0.25, 0.75, 1.25, 1.75
result: 1.284025 2.117 3.490343 5.754602
```


<!-- cannbot:related:start -->
## 相关

- [ForeachExp 950 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_exp_950.md)（`related`）：ForeachExp950 的 R-001 路线是“FLOAT32 值直接传给 `expf`”；expf API执行“根据输入x，获取e的x次方的计算结果。”。API语义支撑每线程标量指数计算和特殊值验证。
- [ForeachSigmoid 950 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_sigmoid_950.md)（`related`）：功能：根据输入x，获取e的x次方的计算结果。；`ComputeSigmoid` 无论 T 为 half、float 还是 BF16，都先转 float，按 `-x -> expf -> +1 -> reciprocal` 计算，再 cast 回 T。API 是 ForeachSigmoid 950 内部 sigmoid 标量链的核心函数。

<!-- cannbot:api-operator:start -->
### 知识正文中的调用示例

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [Softmax 950 Direct Invoke 算子知识](../../../../operators/direct/nn/activation/softmax_950.md)（`related`）：算子正文包含对 `expf(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
