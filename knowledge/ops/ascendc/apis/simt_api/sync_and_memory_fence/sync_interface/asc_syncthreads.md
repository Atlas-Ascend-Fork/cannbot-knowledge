---
type: API
title: AscSyncthreads
description: 阻塞当前线程块内所有线程直到所有线程到达同步点，确保同步点前的内存操作对块内所有线程可见，常用于数据共享和并行归约。
tags:
- task.lookup
- topic.implementation.synchronization
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/sync_and_memory_fence/sync_interface/asc_syncthreads.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/device_sync_functions.h
---

# asc\_syncthreads

## 功能说明

在SIMT（Single Instruction Multiple Threads）编程范式中，同一个线程块（Block）内的多个线程并行执行，但各线程的执行进度可能不同。当需要线程间协调工作、共享数据或确保某些操作按顺序执行时，必须使用同步机制。

asc\_syncthreads接口用于**阻塞当前线程块内所有线程**，直到所有线程都执行到该同步点位置。

**关键特征：**

- 该接口会阻塞线程执行，直到块内所有线程都到达同步点；
- 确保同步点之前的所有内存操作对块内所有线程可见；
- 常用于线程块内的数据共享、分阶段计算、并行归约等场景；

下图展示了同一个线程块内多线程共享数据场景可能出现的问题：

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/syncthreads_1.png)

asc\_syncthreads接口的执行流程示意图如下：

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/syncthreads_function.png)

需要注意，线程块内所有线程必须都调用到asc\_syncthreads\(\)接口，程序才能继续执行。如果有线程未到达同步点，其他线程将被阻塞等待，导致死锁，例如：若将本接口的调用放在分支中，就可能导致部分线程到达不了同步接口调用处，导致程序卡死。

## 函数原型

```cpp
inline void asc_syncthreads()
```

## 参数说明

无

## 返回值说明

无

## 约束说明

- 线程块内所有线程必须都执行到同步点，否则会导致死锁。

- 避免分支中调用本接口，除非能确保线程块内所有线程都进入该分支。
- 避免在循环次数不一致的情况下调用。

## 需要包含的头文件

使用该接口需要包含`simt_api/device_sync_functions.h`头文件。

```cpp
#include "simt_api/device_sync_functions.h"
```

## 调用示例

完整样例请参考[MemoryFence样例](https://gitcode.com/cann/asc-devkit/blob/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/03_simt_api/02_features/01_api_features/01_sync_instruction/memory_fence/README.md)。

- SIMT编程场景：

    ```cpp
    __global__ __launch_bounds__(1024) void kernel_sync_threads(float* dst, int count)
    {
         int idx = threadIdx.x;
         if (idx > 0 && idx < count) {
             dst[idx] = 1;
         }

         // 等待block内所有thread都执行到当前代码
         asc_syncthreads();

         if (idx == 0) {
             dst[0] = 0;
             for(int i = 1023; i > 0; i--) {
                 if (i < count) {
                     dst[0] += dst[i];
                 }
             }
         }
    }
    ```

    ```text
    输出结果:
    [1023, 1, 1, 1 …]
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void kernel_sync_threads(__gm__ float* dst, int count)
    {
         int idx = threadIdx.x;
         if (idx > 0 && idx < count) {
             dst[idx] = 1;
         }

         // 等待block内所有thread都执行到当前代码
         asc_syncthreads();

         if (idx == 0) {
             dst[0] = 0;
             for(int i = 1023; i > 0; i--) {
                 if (i < count) {
                     dst[0] += dst[i];
                 }
             }
         }
    }
    ```

    ```text
    输出结果:
    [1023, 1, 1, 1 …]
    ```


<!-- cannbot:related:start -->
## 相关

- [同步机制（AI Core SIMT编程）](../../../../guides/programming_guide/programming_model/ai_core_simt_programming/synchronization.md)（`explains`）：“- 需要Thread Block内所有Thread完成某一阶段后再继续执行时，使用同步屏障。”与“asc_syncthreads接口用于阻塞当前线程块内所有线程，直到所有线程都执行到该同步点位置。”提供双方正文证据。编程指南给出 Thread Block 阶段同步的选择规则，AscSyncthreads 卡定义阻塞直到全员到达的具体屏障语义，指南解释该接口何时使用。
- [AscThreadfence](../memory_fence/asc_threadfence.md)（`related`）：“不阻塞线程，仅约束可见性顺序”说明 asc_threadfence 不是执行会合点，“阻塞当前线程块内所有线程，直到所有线程都执行到该同步点位置”则提供块内会合，二者共同决定共享数据发布协议。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 2 / 2 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Sort 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/sort_950.md)（`related`）：算子声明的固定版本源码包含对 `asc_syncthreads(...)` 的直接调用（第 1453 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/sort/op_kernel/arch35/sort_radix_sort_more_core.h#L1453)
- [NLLLoss2d 950 ACLNN 算子知识](../../../../operators/aclnn/nn/loss/nll_loss2d_950.md)（`related`）：算子声明的固定版本源码包含对 `asc_syncthreads(...)` 的直接调用（第 65 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/loss/nll_loss/op_kernel/arch35/nll_loss_simt.h#L65)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
