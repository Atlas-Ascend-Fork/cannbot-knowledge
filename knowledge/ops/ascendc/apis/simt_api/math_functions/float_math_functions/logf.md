---
type: API
title: 数学函数logf
description: 获取以e为底，输入数据的对数。 !
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/logf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/math_functions.h
---

# logf

## 功能说明

获取以e为底，输入数据的对数。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002516816339.png)

## 函数原型

```cpp
inline float logf(float x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

以e为底的x的对数。

-   当x小于0或x为nan时，返回值为nan。
-   当x为0时，返回值为-inf。
-   当x为inf时，返回值为inf。

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
    __global__ __launch_bounds__(256) void compute_logf(float *result, const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = logf(x[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(256) inline void compute_logf_vf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = logf(x[idx]);
    }

    __global__ __vector__ void run_logf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        asc_vf_call<compute_logf_vf>(dim3(256), result, x, count);
    }
    ```

输入输出示例如下：

```
x：1, 2, 3, 4
result: 0 0.6931472 1.098612 1.386294
```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 2 / 2 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [SimThreadExponential 950 ACLNN 算子知识](../../../../operators/aclnn/math/random/sim_thread_exponential_950.md)（`related`）：算子声明的固定版本源码包含对 `logf(...)` 的直接调用（第 322 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/random/random_common/op_kernel/arch35/random_kernel_base.h#L322)
- [ForeachLog 950 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_log_950.md)（`related`）：算子声明的固定版本源码包含对 `logf(...)` 的直接调用（第 50 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_log/op_kernel/arch35/foreach_log_simt.h#L50)

### 知识正文中的调用示例

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [CrossEntropyLoss 950 Direct Invoke 算子知识](../../../../operators/direct/nn/loss/cross_entropy_loss_950.md)（`related`）：算子正文包含对 `logf(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
